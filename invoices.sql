SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[Invoices](
	[orderID] [int] IDENTITY(1,1) NOT NULL,
	[orderDetails] [nvarchar](max) NULL,
	[totalPrice] [decimal](10, 2) NULL,
	[date] [date] NULL,
	[concat] [nvarchar](max) NULL,
PRIMARY KEY CLUSTERED 
(
	[orderID] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO