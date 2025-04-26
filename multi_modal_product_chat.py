import chainlit as cl
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
 
import audioop
import base64
from mimetypes import guess_type
from io import BytesIO
import wave
import httpx
import numpy as np
import requests
import os
import urllib.parse
from sqlalchemy import create_engine
import pyodbc
 
import json
from decimal import Decimal
from datetime import date
 
from pydantic import BaseModel
from openai import AzureOpenAI
 
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from typing import List, Optional
 
from dotenv import load_dotenv
 
load_dotenv()
 
 
# Define a threshold for detecting silence and a timeout for ending a turn
SILENCE_THRESHOLD = 3500 # Adjust based on your audio level (e.g., lower for quieter audio)
SILENCE_TIMEOUT = 1300.0 # Seconds of silence to consider the turn finished
username_global=[]
password_global=[]
useremail_global=None
 
AZURE_SEARCH_CONFIG = {
    "endpoint": os.getenv("AI_SEARCH_ENDPOINT"),
    "index_name": os.getenv("index_name"),
    "api_key": os.getenv("AI_SERACH_API_KEY")
}
 
# Example Native Plugin (Tool)
azure_chat_completion = AzureChatCompletion(
                                            api_key=os.getenv("api_key"),
                                            deployment_name="gpt-4",
                                            endpoint=os.getenv("endpoint"),
                                            api_version=os.getenv("api_version")
                                        )
 
connection_string = os.getenv("CONNECTION_STRING")
 
 
class OrderDetails:
    def __init__(self, orderDetails: str, totalPrice: Decimal, date: date, concat: str, id: int):
        self.orderDetails = orderDetails
        self.totalPrice = totalPrice
        self.date = date
        self.concat = concat
        self.id = id
 
class OrderPlugin:
    def __init__(self):
        self.connection_string = connection_string
 
    @kernel_function(
        name="get_orders",
        description="Gets the list of all orders"
    )
    def get_orders(self) -> str:
        orders = self._fetch_order_details()
        # Convert the list of OrderDetails objects to a list of dictionaries
        orders_dict = [
            {
                'orderDetails': order.orderDetails,
                'totalPrice': float(order.totalPrice),  # Convert Decimal to float or str
                'date': order.date.isoformat(),  # Convert date to ISO 8601 string
                'concat': order.concat,
                'id': order.id
            }
            for order in orders
        ]
        # Serialize the list of dictionaries to a JSON string
        orders_json = json.dumps(orders_dict)
        return orders_json
 
    def _fetch_order_details(self) -> List[OrderDetails]:
        orders = []
        conn = pyodbc.connect(self.connection_string)
        cursor = conn.cursor()
        cursor.execute("SELECT orderID, orderDetails, totalPrice, date, concat FROM dbo.[Invoices]")
        rows = cursor.fetchall()
        for row in rows:
            od = OrderDetails(
                id=row.orderID,
                orderDetails=row.orderDetails,
                totalPrice=row.totalPrice,
                date=row.date,
                concat=row.concat
            )
            orders.append(od)
        conn.close()
        return orders
   
class SQLPlugin:
    """Plugin that adds data to SQL table"""
    def __init__(self, connection_string):
        self.connection_string = connection_string
 
    @kernel_function(
        name="insert_invoice",
        description="Insert order details from invoice into SQL Tables"
    )
 
    def insert_invoice(self, invoice_data):
        """Inserts data into SQL Table"""
        conn = pyodbc.connect(self.connection_string)
        cursor = conn.cursor()
        try:
            # Connect to the SQL Server
            # Prepare the SQL INSERT statement
            sql_insert = """
            INSERT INTO dbo.Invoices (orderDetails, totalPrice, date, concat)
            VALUES (?, ?, ?, ?)
            """
 
            # Extract data from JSON
            orderDetails = ', '.join(invoice_data.get("orderDetails", []))
            totalPrice = invoice_data.get("totalPrice")
            date = invoice_data.get("date")
            concat = invoice_data.get("concat")
 
            # Execute the SQL statement
            cursor.execute(sql_insert, (orderDetails, totalPrice, date, concat))
            conn.commit()
 
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Close the connection
            cursor.close()
            conn.close()
     
 
# Example usage
 
 
# Azure AI Search Plugin Implementation
class ProductSearchPlugin:
    """Plugin that provides product search capabilities using Azure AI Search"""
   
    def __init__(self):
        # Initialize Azure AI Search client
        self.client = SearchClient(
            endpoint=AZURE_SEARCH_CONFIG["endpoint"],
            index_name=AZURE_SEARCH_CONFIG["index_name"],
            credential=AzureKeyCredential(AZURE_SEARCH_CONFIG["api_key"])
        )
   
    @kernel_function(
        name="search_products",
        description="Searches for products in Azure AI Search and returns availability information"
    )
    async def search_products(self, product_name: str, quantity: str = "1") -> str:
        """Searches product catalog and returns structured availability data"""
       
        # Perform the search
        results = self.client.search(
            search_text=product_name,
            include_total_count=True,
            top=5,
            select=[
                "ITEMNUMBER", "PRODUCTNAME","MRP", "APPPRODUCTDESCRIPTION"
            ]
        )
       
        if results.get_count() == 0:
            return f"Product '{product_name}' not found in inventory"
       
        # Process results and format response
        products = []
        for result in results:
            product = {
                "product_id": result["ITEMNUMBER"],
                "product_name": result["PRODUCTNAME"],
                "price": (result["MRP"]),
                "description": result["APPPRODUCTDESCRIPTION"],
            }
                      
            products.append(product)
 
        return str(products)
 
 
 
 
       
 
@cl.on_chat_start
async def on_chat_start():
 
    cl.user_session.set("username", username_global)
    cl.user_session.set("password", password_global)  
    cl.user_session.set("email", useremail_global)  
    # Setup Semantic Kernel
    kernel = sk.Kernel()
 
    # Add your AI service (e.g., OpenAI)
    # Make sure OPENAI_API_KEY and OPENAI_ORG_ID are set in your environment
    ai_service = azure_chat_completion
    kernel.add_service(ai_service)
 
    search_plugin = ProductSearchPlugin()
    kernel.add_plugin(search_plugin, "ProductSearch")
 
    invoices_plugin = OrderPlugin()
    kernel.add_plugin(invoices_plugin,"Invoices")
 
    sql_plugin = SQLPlugin(connection_string)
    kernel.add_plugin(sql_plugin,"InsertQuery")
 
    product_agent = ChatCompletionAgent(
        service=azure_chat_completion,
        kernel=kernel,
        name="ProductAgent",
        instructions=(
"""As a Product Information Specialist, your task is to deliver detailed  product information to inquiries from the RouterAgent. Follow these guidelines:
Responsibilities and Procedures
1.Always Utilize the ProductSearch Plugin to gather accurate and up-to-date product information.
2.Provide Detailed Product Descriptions: Offer comprehensive details about products, including specifications and features.
3.Respond to requests for available products by listing items from the knowledge base.
4.Answer Product Specification Queries: Address inquiries regarding product specifications with verified information.
Important Guidelines
-Always verify product information using the search_products function before responding.
-If you are unsure about a product or cannot find it, state "I don't know" rather than guessing.
DO NOT suggest similar alternatives outside the ProductSearch knowledge base."""
        )
    )
 
    billing_agent = ChatCompletionAgent(
        service=azure_chat_completion,
        name="BillingAgent",
        instructions=(
"""Billing and Payment Inquiry Handling Responsibilities:
1. Address all inquiries related to billing and payments
2. Provide detailed explanations of charges
3. Process refund requests
4. Clarify billing policies
 
Required Information:
- Order number
- Date of purchase
- Last 4 digits of payment method
 
Communication Guidelines:
- Maintain professionalism
- Show empathy
- Ensure clarity"""
        )
    )
 
 
    fetch_orders_agent = ChatCompletionAgent(
    service=azure_chat_completion,
    kernel=kernel,
    name="InvoiceAgent",
    instructions=("""
You are an Invoice Agent. Your primary task is to retrieve "order" details from a SQL database using the get_orders function of the Invoices plugin.
AFTER YOU RETRIVE ORDER DETAILS DO NOT SHOW ALL THE ORDER DEATILS, GET SOME INFORMATION FROM USER TO THE SPECIFIC INVOICE
Customers may ask about details of any orders they have placed, which are stored in the Invoices table.
Data Structure:
The function return "order" data json which have columns: orderID, orderDetails, totalPrice, date, concat
Steps and Guidelines:
Retrieve Orders:
Use the get_orders function to fetch "order" values,DON"T show all the invoice
Afterthat,ask the User which Invoice details wants to see
Identify Specific Order:
Analyze the user's input to determine which particular order they are asking about.
Provide the relevant "concat" attribute of the identified order.
IMPORTANT: Do Not Generate Random Values provide information that matches the user's query""")
    )
 
 
    query_agent = ChatCompletionAgent(
    service=azure_chat_completion,
    kernel=kernel,
    name="QueryAgent",
    instructions=("""
You are expert in SQL query.Your primary task is to insert invoice data into an SQL database using the insert_invoice function of the InsertQuery plugin.
The JSON Structure you will receive:
{
"orderDetails": [
    "Product 1, Quantity: 2, UnitPrice: 10.00",
    "Product 2, Quantity: 5, UnitPrice: 20.00"
],
"totalPrice": 110.00,
"date": "2023-10-07",// here use todays date
"concat": "Example Product 1, Quantity: 2, UnitPrice: 10.00 Example Product 2, Quantity: 5, UnitPrice: 20.00 110.00 2023-10-07"
}
- The columns of the table Invoices are  orderDetails,totalPrice,date,concat
Invoice Verification:
 
Use select_invoice to check for existing entries with matching concat values in the Invoices table.
If a match is found, do not insert the current data to prevent duplicates.""")
    )
 
   
    order_agent = ChatCompletionAgent(
        service=azure_chat_completion,
        kernel=kernel,
        name="OrderAgent",
        plugins=[query_agent],
        instructions=(
"""Your role is to understand and process product-related requests efficiently.
Follow the steps:
Product Identification:Identify Product Name, Price, and Quantity from the request.
Verify Information:Use the search_products tool to confirm product existence and retrieve pricing details.
Invoice Generation:Compute subtotals for each product and the overall total amount due and provide invoice
Format Invoice:
Product Name | Quantity | Unit Price | Total Price
product1     | qty1     | price1     | total1
product2     | qty2     | price2     | total2
---
Total Amount Due: $total
Final Steps:  
    SEND Invoice details to -> QueryAgent in JSON format:
{
"orderDetails": [
    "Product 1, Quantity: 2, UnitPrice: 10.00",
    "Product 2, Quantity: 5, UnitPrice: 20.00"
],
"totalPrice": 110.00,
"date": "2023-10-07",
"concat": "Example Product 1, Quantity: 2, UnitPrice: 10.00 Example Product 2, Quantity: 5, UnitPrice: 20.00 110.00 2023-10-07"
}
Use the current date for "date".
"""
        )
    )
 
    router_agent = ChatCompletionAgent(
        service=azure_chat_completion,
        kernel=kernel,
        name="RouterAgent",
        instructions=(
        """
You are an AI assistant named GROOT.
When responding, use a warm and professional tone.If you are unsure about an answer, it's okay to say you don't know rather than guessing.
As "Groot," the intelligent AI Router Assistant for customer queries, your role is to efficiently direct user inquiries to the appropriate specialist agents.
 
Query Analysis and Routing:
 
    Product Information:
        Route to: ProductAgent
        Keywords to identify: "product info," "what is," "tell me about," "price of"
 
    Billing/Payment:
        Route to: BillingAgent
        Keywords to identify: "invoice," "charge," "refund," "payment"
 
    Order Details:
        Route to: InvoiceAgent
        Keywords to identify: "previous order," "order details"
     
 
    Orders:
        Route to: OrderAgent
        Keywords to identify: "order," "purchase," "buy," "I want," "add to cart"
 
    Ambiguous Requests:
        Action: Ask clarifying questions to better understand the user's needs
 
Guidelines and Tone:
    Delegation: Always delegate queries to the relevant specialist agents. Never provide direct answers yourself.
    Context Maintenance: Keep track of the conversation context for seamless interactions.
    Data Limitation: Provide responses only based on the supplied data knowledge and when required use ProductQuery plugin tool. Avoid using web knowledge.
 
Communication Style:
    Use a friendly and conversational tone.
    Write in short, concise sentences and paragraphs.
    Prefer the active voice.
    Avoid jargon or technical terms unless necessary.
    Use bullet points or numbered lists for clarity and readability.
    Ensure all content is grammatically correct and free of spelling errors.
 
IMPORTANT NOTE:
    If a query cannot be addressed with the available data, respond with "I don't know" rather than attempting to generate information.
        """
        ),
        plugins=[product_agent, billing_agent, order_agent,fetch_orders_agent]
    )
   
    # Instantiate and add the Chainlit filter to the kernel
    # This will automatically capture function calls as Steps
    sk_filter = cl.SemanticKernelFilter(kernel=kernel)
 
    agent = ChatCompletionAgent(
        kernel=kernel,
        name="Host",
        instructions="You are a helpful assistant",
    )
 
    thread: ChatHistoryAgentThread = None
    cl.user_session.set("agent", agent)
    cl.user_session.set("thread", thread)
 
 
@cl.set_chat_profiles
async def chat_profile(current_user: cl.User):
   
    return [
        cl.ChatProfile(
            name="Groot",
            icon="https://cdn-icons-png.freepik.com/256/869/869636.png",
            markdown_description="Hey there! I am Groot. How may I help you?",
            starters=[
                cl.Starter(
                label="New Orders",
                message="I want to order something new!",
                icon="https://www.freeiconspng.com/uploads/red-simple-shopping-cart-icon-12.png"
                ),
 
                cl.Starter(
                label="Get Order Details",
                message="Give me my previous order details",
                icon = "https://cdn2.iconfinder.com/data/icons/thin-line-color-1/21/29_1-512.png"
                ),
                cl.Starter(
                label="Browse Products",
                message="I want to browse product catalogues",
                icon="https://static.vecteezy.com/system/resources/thumbnails/028/047/001/small_2x/3d-box-icon-free-png.png"
                ),
            ],    
        )            
    ]
 
@cl.step(type="tool")
async def speech_to_text(audio_buffer):
 
    client_whisper = AzureOpenAI(
        api_key= os.getenv("whisper_api_key"),  
        api_version=os.getenv("whisper_api_version"),
        azure_endpoint =os.getenv("whisper_azure_endpoint")
    )
     
    result = client_whisper.audio.transcriptions.create(
        file=audio_buffer,            
        model="whisper"
    )
 
    #print(result.text)
    return result.text
 
@cl.step(type="tool")
async def process_audio():
 
      # Get the audio buffer from the session
    if audio_chunks := cl.user_session.get("audio_chunks"):
        # Concatenate all chunks
        concatenated = np.concatenate(list(audio_chunks))
 
        # Create an in-memory binary stream
        wav_buffer = BytesIO()
 
        # Create WAV file with proper parameters
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
            wav_file.setframerate(24000)  # sample rate (24kHz PCM)
            wav_file.writeframes(concatenated.tobytes())
 
        # Reset buffer position
        wav_buffer.seek(0)
 
        cl.user_session.set("audio_chunks", [])
 
    frames = wav_file.getnframes()
    rate = wav_file.getframerate()
 
    duration = frames / float(rate)
    if duration <= 1.71:
        print("The audio is too short, please try again.")
        return
 
    audio_buffer = wav_buffer.getvalue()
    input_audio_el = cl.Audio(content=audio_buffer, mime="audio/wav")
    whisper_input = ("audio.wav", audio_buffer, "audio/wav")
 
    transcription = await speech_to_text(whisper_input)
    voice_response = "This is the user response: \n"+transcription
    await cl.Message(voice_response).send()
 
    agent = cl.user_session.get("agent") # type
    thread = cl.user_session.get("thread") # type: ChatHistoryAgentThread
 
    answer = cl.Message(content="")
 
    async for response in agent.invoke_stream(messages=transcription, thread=thread):
 
        if response.content:
            await answer.stream_token(str(response.content))
 
        thread = response.thread
        cl.user_session.set("thread", thread)
 
    # Send the final message
    await answer.send()
       
    with open("output.wav", "wb") as wav_file:
    # Write bytes to file
        wav_file.write(audio_buffer)
       
 
@cl.on_audio_start
async def on_audio_start():
    cl.user_session.set("silent_duration_ms", 0)
    cl.user_session.set("is_speaking", False)
    cl.user_session.set("audio_chunks", [])
    # await cl.Message(content="audio starts.").send()
    return True
 
@cl.on_audio_end
async def on_audio_end():  
    pass
 
@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    audio_chunks = cl.user_session.get("audio_chunks")
   
    if audio_chunks is not None:
        #await cl.Message(content="adding audio chunk..").send()
        audio_chunk = np.frombuffer(chunk.data, dtype=np.int16)
        audio_chunks.append(audio_chunk)
        cl.user_session.set("audio_chunks", audio_chunks)
 
    # If this is the first chunk, initialize timers and state
    if chunk.isStart:
        #--------
        cl.user_session.set("silent_duration_ms", 0)
        cl.user_session.set("is_speaking", False)
        cl.user_session.set("audio_chunks", [])
        #----------
        #await cl.Message(content="first audio chunk..").send()
        cl.user_session.set("audio_mime_type", chunk.mimeType)
        #cl.user_session.set("name",f"input_audio.{chunk.mimeType.split('/')[1]}")
        cl.user_session.set("name",f"Test")
        cl.user_session.set("last_elapsed_time", chunk.elapsedTime)
        cl.user_session.set("is_speaking", True)
        return
 
    audio_chunks = cl.user_session.get("audio_chunks")
    last_elapsed_time = cl.user_session.get("last_elapsed_time")
    silent_duration_ms = cl.user_session.get("silent_duration_ms")
    is_speaking = cl.user_session.get("is_speaking")
 
    # Calculate the time difference between this chunk and the previous one
    time_diff_ms = chunk.elapsedTime - last_elapsed_time
    cl.user_session.set("last_elapsed_time", chunk.elapsedTime)
 
    # Compute the RMS (root mean square) energy of the audio chunk
    audio_energy = audioop.rms(chunk.data, 2)  # Assumes 16-bit audio (2 bytes per sample)
 
    if audio_energy < SILENCE_THRESHOLD:
        # Audio is considered silent
        silent_duration_ms += time_diff_ms
        cl.user_session.set("silent_duration_ms", silent_duration_ms)
        if silent_duration_ms >= SILENCE_TIMEOUT and is_speaking:
            cl.user_session.set("is_speaking", False)
            await process_audio()
            #await cl.Message(content="This is an audio response.").send()
    else:
        # Audio is not silent, reset silence timer and mark as speaking
        cl.user_session.set("silent_duration_ms", 0)
        if not is_speaking:
            cl.user_session.set("is_speaking", True)
 
 
@cl.on_message
async def on_message(message: cl.Message):
    agent = cl.user_session.get("agent") # type
    thread = cl.user_session.get("thread") # type: ChatHistoryAgentThread
    query: str
    if message.elements:
        images = [file for file in message.elements if "image" in file.mime]
        mime_type, _ = guess_type(images[0].path)
        if mime_type is None:
            mime_type = 'application/octet-stream'  # Default MIME type if none is found
 
        with open(images[0].path, "rb") as image_file:
            base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')
 
        file_contents = f"data:{mime_type};base64,{base64_encoded_data}"
 
        api_base_4o = os.getenv("endpoint") # os.getenv("endpoint")
        api_key_4o = os.getenv("api_key")
        deployment_name_4o = 'gpt-4o'
        api_version_4o = os.getenv("api_version") # this might change in the future
 
        client = AzureOpenAI(
            api_key=api_key_4o,  
            api_version=api_version_4o,
            base_url=f"{api_base_4o}openai/deployments/{deployment_name_4o}",
        )
 
        response_img = client.chat.completions.create(
        model= 'gpt-4o',
            messages=[
                { "role": "system", "content": "You are a helpful assistant." },
                { "role": "user", "content": [  
                    {
                        "type": "text",
                        "text": message.content
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": file_contents
                        }
                    }
                ] }
            ],
            max_tokens=2000
        )
        query = response_img.choices[0].message.content
    else:
        query = message.content
 
    answer = cl.Message(content="")
 
    async for response in agent.invoke_stream(messages=query, thread=thread):
 
        if response.content:
            await answer.stream_token(str(response.content))
 
        thread = response.thread
        cl.user_session.set("thread", thread)
 
    # Send the final message
    await answer.send()
 
 
@cl.password_auth_callback
def auth_callback(username: str, password: str):
   
    conn = pyodbc.connect(os.getenv("CONNECTION_STRING"))
    cursor = conn.cursor()
    print("passed username and password\n")
    print(username, password)
    cursor.execute("SELECT username, password,usertype, emailid FROM dbo.[USER] WHERE username = ? AND password = ?", (username, password))
    row = cursor.fetchone()
    print(row)
    username_stored=row[0]
    password_stored=row[1]
    usertype=row[2]
    emailstore=row[3]
    usertype_global = usertype
    useremail_global=emailstore
    conn.close()
 
    print(username_stored, password_stored)
    if username_stored is None or password_stored is None:
        raise ValueError(
            "Username or password dont exist"
        )
 
    if (username, password) == (username_stored, password_stored):
        loggeduser = username
 
        username_global.append(username)
        password_global.append(password)
       
        return cl.User(
            identifier=username, metadata={"role": usertype, "provider": "credentials"}
 
 
        )
   
 
    else:
        return None