import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

import requests
import urllib.parse
from sqlalchemy import create_engine
import pyodbc
from typing import List, Optional

class OrderDetails:
  def __init__(self, orderDetails: str, totalPrice: str, date: str, concat: str,id: int):       
     self.orderDetails = orderDetails
     self.totalPrice = totalPrice
     self.date = date
     self.concat = concat
     self.id = id

class OrderPlugin:
   def __init__(self):
     connection_string = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=trainingserver2023.database.windows.net;DATABASE=training2023db;UID=serveradmin_lokesh44;PWD=123456789Aa'

   @kernel_function(
        name="get_orders",
        description="Gets the list of all orders"
    )
   def get_orders(self) -> List[OrderDetails]:
     return self._fetch_order_details()

#    def get_orderIds(self, orderInfo: str) -> List[OrderDetails]:
#      return [item.dat for item in self._fetch_order_details()]

   @kernel_function(
        name="get_total_price",
        description="Get the total price of a particular order"
    )
   def get_total_price(self, order_id: str) -> Optional[float]:
    for item in self._fetch_order_details():
        if item.id == order_id:
            return item.totalPrice
    return None

   def _fetch_order_details(self) -> List[OrderDetails]:
     orders = []
     conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=vectortest.database.windows.net;DATABASE=vectortest;UID=vectorAdmin;PWD=005ikaytaS#')
     cursor = conn.cursor()
     cursor.execute("SELECT id, orderDetails,totalPrice, date, concat FROM dbo.[Invoices]") #WHERE username = ? AND password = ?", (username, password))
     rows = cursor.fetchall()
     for row in rows:
       od = OrderDetails(id=row[0],orderDetails=row[1],totalPrice=row[2],date=row[3],concat=row[4])
       orders.append(od)
     conn.close()
     return orders

# Example usage:
# plugin = MenuPlugin(r"C:\Users\dpal026\OneDrive - pwc\Desktop\Azure AI\AgenticAI\Semantic Kernel\semantic-kernel\dotnet\samples\GettingStartedWithAgents\Plugins\menu.csv")
# print(plugin.get_menu())
# print(plugin.get_specials())
# print(plugin.get_item_price("Pizza"))
