
# Multi-Modal Retail Chatbot using Gen AI Agentic Applications

- Using Semantic Kernel, Chainlit, Azure AI Search, SSMS & Azure AI Foundry, this end-to-end Retail chatbot can browse products, take orders, and get details of previous orders by interacting with the user using natural language. 
- It has in-built multi-modality, allowing inputs through voice, texts, and even images.

## Steps to Run the Code

1. **Install Dependencies:**
   
   ```
     pip install -r requirements.txt
   ```

2. **Configure SQL Server:**

    - Provide the connection string of your SQL server in the ***.env*** file.
    - Run the ***load_catalog_to_sql.py file***.
   
3. **Set Up Azure AI Search Service:**

    - Go to the Azure portal and create a new AI Search Service.
    - Import data and select your table from the SQL database to create an index and an indexer.
    - Fill up the fields for the AI Search in the ***.env*** file.
      
4. **Provision Azure AI Foundry:**

    - Go to Azure AI Foundry and provision an Azure OpenAI resource.
    - Provision models 4, 4o, and Whisper.
    - Fill relevant fields in the .env file.
      
5. **Set Up Literal AI:**

    - Go to Literal AI and create a new project.
    - Fill up the Literal API key in the .env file.
  
6) Chainlit Authentication:

    In your terminal, run:

    ```
     chainlit create-secret
    ```
8)  Run SQL Scripts:

    - Execute the ***users.sql*** and ***invoices.sql*** scripts in your query editor.
      
10) Run the Application:

    In the terminal, run:
   
    ```
     chainlit run multi_modal_product_chat.py -w
    ```

11)  Copy the contents of the ***config_edit.toml*** file and paste them in the ***config.toml*** file the newly created chainlit folder and reload the web page.
    
12)  On the login page, use the following credentials:
        - Username: john.doe
        - Password: dummyPassword1

That's it, you are good to go!

