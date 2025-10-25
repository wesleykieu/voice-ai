from livekit.agents import function_tool, RunContext
import json
import os
import logging
import chromadb
from chromadb.config import Settings
from datetime import datetime
import uuid

logger = logging.getLogger("memory_tools")


class MemoryTools:
    def __init__(self, storage_dir="user_memories"):
        self.storage_dir = storage_dir
        self.client = None
        self.collections = {}

        # Create storage directory
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)

        # Initialize ChromaDB
        self._init_chroma()

    def _init_chroma(self):
        """Initialize ChromaDB client"""
        try:
            # Create persistent ChromaDB client
            self.client = chromadb.PersistentClient(
                path=os.path.join(self.storage_dir, "chromadb"),
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )
            logger.info("ChromaDB initialized successfully")
            
            # Load static memories from JSON file
            self._load_static_memories()
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise

    def _load_static_memories(self):
        """Load memories from the static JSON file into ChromaDB"""
        try:
            # Path to the static memories file
            memories_file = os.path.join(os.path.dirname(__file__), "..", "data", "memories.json")
            
            if not os.path.exists(memories_file):
                logger.info("No static memories file found")
                return
                
            with open(memories_file, "r", encoding="utf-8") as f:
                memories_data = json.load(f)
            
            # Get the default user collection
            collection = self._get_collection("default_user")
            
            # Check if memories are already loaded
            if collection.count() > 0:
                logger.info("Static memories already loaded")
                return
            
            # Load all memories from the JSON file
            memory_id = 0
            for category, memories in memories_data.items():
                if category == "person":
                    # Store personal info as a memory
                    person_info = memories
                    content = f"My name is {person_info.get('name', 'Maggie')}. I was born on {person_info.get('birth_date', 'April 15, 1932')} in {person_info.get('birth_place', 'Brooklyn, New York')}. I'm {person_info.get('current_age', 92)} years old and I was a {person_info.get('profession', 'Elementary School Teacher')}. My favorite flower is {person_info.get('favorite_flower', 'yellow roses')} and I enjoy {', '.join(person_info.get('hobbies', ['reading', 'gardening']))}."
                    
                    collection.add(
                        documents=[content],
                        metadatas=[{
                            "category": "personal_info",
                            "title": "About Me",
                            "year": "1932",
                            "added_at": datetime.now().isoformat(),
                        }],
                        ids=[f"static_{memory_id}"],
                    )
                    memory_id += 1
                    
                elif isinstance(memories, list):
                    # Load all memory categories
                    for memory in memories:
                        if isinstance(memory, dict) and "description" in memory:
                            content = memory["description"]
                            title = memory.get("title", "Memory")
                            year = memory.get("year", memory.get("age", ""))
                            
                            collection.add(
                                documents=[content],
                                metadatas=[{
                                    "category": category,
                                    "title": title,
                                    "year": str(year),
                                    "added_at": datetime.now().isoformat(),
                                }],
                                ids=[f"static_{memory_id}"],
                            )
                            memory_id += 1
            
            logger.info(f"Loaded {memory_id} static memories into ChromaDB")
            
        except Exception as e:
            logger.error(f"Error loading static memories: {e}")

    def _get_user_id(self, context: RunContext) -> str:
        """Get user ID from context (room name)"""
        return context.room.name if hasattr(context, "room") else "default_user"

    def _get_collection(self, user_id: str):
        """Get or create a collection for the user"""
        if user_id in self.collections:
            return self.collections[user_id]

        try:
            # Create a safe collection name (ChromaDB has naming restrictions)
            collection_name = f"user_{user_id.replace('-', '_').replace(' ', '_')}"

            # Get or create collection with built-in embeddings
            collection = self.client.get_or_create_collection(
                name=collection_name, metadata={"user_id": user_id}
            )

            self.collections[user_id] = collection
            logger.info(f"Collection ready for user: {user_id}")
            return collection
        except Exception as e:
            logger.error(f"Error getting collection: {e}")
            raise

    def _get_metadata_file(self, user_id: str) -> str:
        """Get path to user's metadata file (for personal info)"""
        return os.path.join(self.storage_dir, f"{user_id}_metadata.json")

    def _load_metadata(self, user_id: str) -> dict:
        """Load user's metadata (personal info)"""
        file_path = self._get_metadata_file(user_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")

        return {"personal_info": {}, "created_at": datetime.now().isoformat()}

    def _save_metadata(self, user_id: str, metadata: dict):
        """Save user's metadata"""
        metadata["updated_at"] = datetime.now().isoformat()
        file_path = self._get_metadata_file(user_id)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            raise

    @function_tool
    async def store_personal_info(
        self, context: RunContext, info_type: str, value: str
    ):
        """Store basic personal information like name, birthdate, hometown, occupation.

        Args:
            info_type: Type of info (e.g., "name", "birthdate", "hometown", "occupation")
            value: The value to store
        """
        try:
            user_id = self._get_user_id(context)
            metadata = self._load_metadata(user_id)

            metadata["personal_info"][info_type] = value
            self._save_metadata(user_id, metadata)

            logger.info(f"Stored {info_type} for user {user_id}")
            return (
                f"Got it, I've remembered your {info_type.replace('_', ' ')}: {value}"
            )
        except Exception as e:
            logger.error(f"Error storing info: {e}")
            return "I had trouble remembering that. Could you tell me again?"

    @function_tool
    async def add_memory(
        self,
        context: RunContext,
        category: str,
        title: str,
        content: str,
        year: str = "",
    ):
        """Add a life memory or story to the vector database.

        Args:
            category: Category like "childhood", "family", "career", "education", "achievement"
            title: Brief title for the memory
            content: The detailed memory or story
            year: Optional year when this happened
        """
        try:
            user_id = self._get_user_id(context)
            collection = self._get_collection(user_id)

            # Create unique ID for this memory
            memory_id = str(uuid.uuid4())

            # Store in ChromaDB with metadata
            collection.add(
                documents=[content],
                metadatas=[
                    {
                        "category": category,
                        "title": title,
                        "year": year,
                        "added_at": datetime.now().isoformat(),
                    }
                ],
                ids=[memory_id],
            )

            logger.info(f"Added memory '{title}' for user {user_id}")
            return f"Thank you for sharing that memory about {title}. I've saved it."
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return "I had trouble saving that memory. Could you share it again?"

    @function_tool
    async def search_memories(self, context: RunContext, query: str):
        """Search through the user's memories using natural language.

        Args:
            query: Natural language query like "my childhood", "when I was young", "my kids"
        """
        try:
            user_id = self._get_user_id(context)
            collection = self._get_collection(user_id)

            # Check if collection has any memories
            count = collection.count()
            if count == 0:
                return "I don't have any memories stored yet. Would you like to tell me about your life?"

            # Search using ChromaDB's built-in semantic search
            results = collection.query(
                query_texts=[query],
                n_results=2,  # Get top 2 most relevant memories
            )

            if not results["documents"][0]:
                return "I don't have any memories about that yet. Would you like to tell me about it?"

            # Get the most relevant memory
            best_content = results["documents"][0][0]
            best_metadata = results["metadatas"][0][0]

            response = f"I remember you told me: {best_content}"

            if best_metadata.get("year"):
                response += f" That was in {best_metadata['year']}."

            logger.info(f"Found memory for query '{query}' for user {user_id}")
            return response

        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return "I'm having trouble accessing those memories right now."

    @function_tool
    async def get_personal_info(self, context: RunContext):
        """Get the user's basic personal information."""
        try:
            user_id = self._get_user_id(context)
            metadata = self._load_metadata(user_id)
            info = metadata.get("personal_info", {})

            if not info:
                return "I don't have your basic information yet. What would you like to tell me about yourself?"

            parts = []
            if "name" in info:
                parts.append(f"Your name is {info['name']}")
            if "birthdate" in info:
                parts.append(f"you were born on {info['birthdate']}")
            if "hometown" in info:
                parts.append(f"you're from {info['hometown']}")
            if "occupation" in info:
                parts.append(f"you worked as a {info['occupation']}")

            return ". ".join(parts) + "." if parts else "Tell me about yourself."

        except Exception as e:
            logger.error(f"Error getting personal info: {e}")
            return "I'm having trouble accessing that information."

    @function_tool
    async def get_memory_summary(self, context: RunContext):
        """Get a summary of all stored memories."""
        try:
            user_id = self._get_user_id(context)
            collection = self._get_collection(user_id)
            metadata = self._load_metadata(user_id)

            memory_count = collection.count()
            info = metadata.get("personal_info", {})

            if memory_count == 0 and not info:
                return (
                    "We haven't stored any memories yet. I'd love to hear your story!"
                )

            response = f"I have {memory_count} memories stored about your life"

            if info and "name" in info:
                response += f", {info['name']}"

            response += ". What would you like to talk about?"

            logger.info(f"Memory summary for user {user_id}: {memory_count} memories")
            return response

        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            return "I'm having trouble accessing the memories right now."

    @function_tool
    async def search_by_category(self, context: RunContext, category: str):
        """Search memories by category like 'childhood', 'family', 'career', 'education'.

        Args:
            category: The category to search (childhood, family, career, education, achievement)
        """
        try:
            user_id = self._get_user_id(context)
            collection = self._get_collection(user_id)

            # Get all memories and filter by category
            results = collection.get(where={"category": category})

            if not results["documents"]:
                return f"I don't have any memories about {category} yet. Would you like to share some?"

            # Return first memory from category
            content = results["documents"][0]
            metadata = results["metadatas"][0]

            response = f"About your {category}: {content}"
            if metadata.get("year"):
                response += f" This was in {metadata['year']}."

            logger.info(
                f"Found {len(results['documents'])} memories in category '{category}' for user {user_id}"
            )
            return response

        except Exception as e:
            logger.error(f"Error searching by category: {e}")
            return f"I'm having trouble finding {category} memories right now."

    @function_tool
    async def list_categories(self, context: RunContext):
        """List all memory categories that have been used."""
        try:
            user_id = self._get_user_id(context)
            collection = self._get_collection(user_id)

            # Get all memories
            results = collection.get()

            if not results["metadatas"]:
                return "You haven't shared any memories yet. What would you like to tell me about?"

            # Extract unique categories
            categories = set()
            for metadata in results["metadatas"]:
                if "category" in metadata:
                    categories.add(metadata["category"])

            if categories:
                cat_list = ", ".join(sorted(categories))
                return f"You've shared memories about: {cat_list}. What would you like to talk about?"
            else:
                return "You've shared some memories. What would you like to discuss?"

        except Exception as e:
            logger.error(f"Error listing categories: {e}")
            return "I'm having trouble accessing the categories right now."
