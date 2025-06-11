"""
Intelligent Query System for Startup Ecosystem Graph
===================================================

This module uses a Large Language Model (LLM) to translate natural language questions
into Cypher queries for a Neo4j database. It provides a flexible and intuitive way
to explore the startup ecosystem knowledge graph.

**Key Features:**
- **Natural Language to Cypher:** Leverages the Gemini LLM to convert user questions
  into executable Cypher queries.
- **Dynamic Schema Generation:** Automatically inspects the database to create a
  schema, ensuring the LLM has the correct context.
- **Safety First:** Includes a basic validation layer to prevent destructive
  queries from being run.
- **Interactive Session:** Allows for real-time querying of the database.

**Setup:**
1. Install the required library: `pip install google-generativeai`
2. Set your Gemini API key as an environment variable:
   `export GEMINI_API_KEY="YOUR_API_KEY"`
"""

import os
import logging
import pandas as pd
from neo4j import GraphDatabase
import google.generativeai as genai
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- LLM Integration ---
try:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not found.")
    genai.configure(api_key=GEMINI_API_KEY)
    llm = genai.GenerativeModel('gemini-1.5-flash')
    logger.info(" Successfully configured Gemini LLM.")
except Exception as e:
    logger.error(f" Failed to configure Gemini LLM: {e}")
    llm = None

class IntelligentQuerySystem:
    """
    Translates natural language to Cypher queries using an LLM.
    """
    _instance = None

    def __new__(cls, driver, database="neo4j"):
        if cls._instance is None:
            cls._instance = super(IntelligentQuerySystem, cls).__new__(cls)
            cls._instance.driver = driver
            cls._instance.database = database
            cls._instance.schema = None
            cls._instance.prompt_template = None
        return cls._instance

    def _generate_schema(self) -> str:
        """
        Dynamically generates a schema representation from the Neo4j database.
        This is crucial context for the LLM.
        """
        if self.schema:
            return self.schema
        
        logger.info("🛠️ Generating graph schema from database...")
        schema_parts = []
        with self.driver.session(database=self.database) as session:
            # Get node labels and their properties
            labels = session.run("CALL db.labels() YIELD label RETURN label").value('label')
            schema_parts.append("Node Labels and Properties:")
            for label in labels:
                properties = session.run(f"MATCH (n:{label}) WITH n LIMIT 100 "
                                         "UNWIND keys(n) AS key "
                                         "RETURN DISTINCT key").value('key')
                schema_parts.append(f"- {label}: {', '.join(properties)}")

            # Get relationship types and their properties
            rel_types = session.run("CALL db.relationshipTypes() YIELD relationshipType "
                                    "RETURN relationshipType").value('relationshipType')
            schema_parts.append("\nRelationship Types:")
            for rel_type in rel_types:
                # Find relationships and connect nodes
                rel_info = session.run(
                    f"MATCH (a)-[r:`{rel_type}`]->(b) "
                    "RETURN DISTINCT labels(a) AS from, labels(b) AS to LIMIT 1"
                ).single()
                if rel_info:
                    from_labels = rel_info['from']
                    to_labels = rel_info['to']
                    if from_labels and to_labels:
                        from_label = from_labels[0]
                        to_label = to_labels[0]
                        schema_parts.append(f"- ({from_label})-[:{rel_type}]->({to_label})")
        
        self.schema = "\n".join(schema_parts)
        logger.info("✅ Schema generation complete.")
        logger.debug(f"Generated Schema:\n{self.schema}")
        return self.schema

    def _build_prompt(self, user_question: str) -> str:
        """
        Constructs the full prompt to send to the LLM, including schema and examples.
        """
        schema = self._generate_schema()
        
        prompt = f"""You are an expert Neo4j developer. Convert this natural language question into a Cypher query.

**Graph Schema:**
{schema}

**Important Rules:**
- Return ONLY the Cypher query, no explanations
- Use the exact schema provided above
- For string matching, use CONTAINS for flexibility
- Pay attention to the specific question being asked

**Examples:**
User: "How many startups are there?"
Cypher: MATCH (s:Startup) RETURN count(s) AS total_startups

User: "How many startups are in the FinTech industry?"
Cypher: MATCH (s:Startup) WHERE s.industry = 'FinTech' RETURN count(s) AS fintech_startups

User: "What technologies does Robinson use?"
Cypher: MATCH (s:Startup {{name: 'Robinson'}})-[:USES_TECHNOLOGY]->(t:Technology) RETURN t.name AS technology

User: "Which VCs typically co-invest with Williams Ventures?"
Cypher: MATCH (vc1:VC {{name: 'Williams Ventures'}})-[:INVESTS_IN]->(s:Startup)<-[:INVESTS_IN]-(vc2:VC) WHERE vc1 <> vc2 RETURN vc2.name AS co_investor, count(s) AS co_investments ORDER BY co_investments DESC LIMIT 10

User: "If I'm starting an EdTech company, which VCs should I target?"
Cypher: MATCH (vc:VC)-[:INVESTS_IN]->(s:Startup) WHERE s.industry = 'EdTech' RETURN vc.name AS vc_name, count(s) AS edtech_investments ORDER BY edtech_investments DESC LIMIT 10

User: "Top 5 industries by startup count?"
Cypher: MATCH (s:Startup) RETURN s.industry AS industry, count(s) AS startups ORDER BY startups DESC LIMIT 5

**Current Question:** {user_question}

**Cypher Query:**"""
        
        return prompt

    def _is_safe_query(self, query: str) -> bool:
        """
        A simple check to prevent destructive operations.
        """
        query_lower = query.lower()
        unsafe_keywords = ["delete", "detach", "create", "merge", "set", "remove", "drop"]
        if any(keyword in query_lower for keyword in unsafe_keywords):
            logger.warning(f"🚨 Unsafe query detected and blocked: {query}")
            return False
        return True

    def query(self, user_question: str):
        """
        Takes a user's question, generates a Cypher query, executes it, and returns the result.
        """
        if not llm:
            logger.error("LLM not configured. Cannot process query.")
            return "LLM is not available. Please check your API key and configuration."

        try:
            # 1. Build the prompt
            logger.info("Building prompt...")
            prompt = self._build_prompt(user_question)
            
            # 2. Get Cypher query from LLM
            logger.info(f"🤔 Sending question to LLM: '{user_question}'")
            logger.debug(f"Full prompt being sent:\n{prompt}")
            try:
                response = llm.generate_content(prompt)
                cypher_query = response.text.strip().replace("```cypher", "").replace("```", "").strip()
                logger.info(f"🤖 LLM-generated Cypher: {cypher_query}")
            except Exception as e:
                logger.error(f"❌ LLM query generation failed: {e}")
                return f"Error generating query: {e}"

            # 3. Validate and execute the query
            if not self._is_safe_query(cypher_query):
                return "The generated query was blocked for safety reasons (it contained a write operation)."

            logger.info(f"Executing query: {cypher_query}")
            with self.driver.session(database=self.database) as session:
                result = session.run(cypher_query)
                # Convert to pandas DataFrame for nice printing
                records = [record.data() for record in result]
                df = pd.DataFrame(records)
                return df
                
        except Exception as e:
            import traceback
            logger.error(f"❌ Error in query method: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return f"Error in query method: {e}"

def interactive_session(query_system: IntelligentQuerySystem):
    """
    An interactive command-line loop to ask questions.
    """
    print("\n" + "="*60)
    print("🤖 Intelligent Startup Ecosystem Query System")
    print("="*60)
    print("Ask me anything about the startup data!")
    print("Type 'exit' or 'quit' to end the session.")
    
    while True:
        try:
            question = input("\nYour question > ").strip()
            if question.lower() in ['exit', 'quit']:
                print("👋 Goodbye!")
                break
            if not question:
                continue

            result = query_system.query(question)
            
            print("\n" + "-"*30 + " Answer " + "-"*30)
            if isinstance(result, pd.DataFrame):
                if result.empty:
                    print("No results found.")
                else:
                    print(result.to_markdown(index=False))
            else:
                print(result)
            print("-" * 68)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"An error occurred in the interactive session: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    
    # Establish Neo4j connection using environment variables
    try:
        load_dotenv()
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USER", "neo4j") 
        password = os.getenv("NEO4J_PASSWORD")
        database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        if not uri or not password:
            raise ValueError("Please set NEO4J_URI and NEO4J_PASSWORD in your .env file")
        
        driver = GraphDatabase.driver(
            uri, 
            auth=(username, password),
            notifications_min_severity='WARNING'
        )
        
        # Initialize the query system
        iqs = IntelligentQuerySystem(driver, database)
        
        # Start the interactive session
        interactive_session(iqs)
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize the system: {e}")
    finally:
        if 'driver' in locals() and driver:
            driver.close()
            logger.info("Neo4j driver closed.") 