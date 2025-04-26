
SET ANSI_NULLS ON;
GO

SET QUOTED_IDENTIFIER ON;
GO

-- Create the USER table
CREATE TABLE [dbo].USER NULL,
    [password] nvarchar NULL,
    [emailid] nvarchar NULL,
    [usertype] [varcharNULL
) ON [PRIMARY];
GO

-- Insert data into the USER table
INSERT INTO [dbo].[USER] (username, password, emailid, usertype) VALUES
('john.doe', 'dummyPassword1', 'john.doe@example.com', 'user'),
('jane.smith', 'dummyPassword2', 'jane.smith@example.com', 'user'),
('alice.johnson', 'dummyPassword3', 'alice.johnson@example.com', 'user'),
('bob.brown', 'dummyPassword4', 'bob.brown@example.com', 'user'),
('charlie.davis', 'dummyPassword5', 'charlie.davis@example.com', 'user'),
('diana.evans', 'dummyPassword6', 'diana.evans@example.com', 'user'),
('ethan.harris', 'dummyPassword7', 'ethan.harris@example.com', 'user'),
('fiona.green', 'dummyPassword8', 'fiona.green@example.com', 'user'),
('george.hill', 'dummyPassword9', 'george.hill@example.com', 'user'),
('hannah.king', 'dummyPassword10', 'hannah.king@example.com', 'user'),
('manashi sarkar', 'manashi123', 'manashi.sarkar@example.com', 'admin');
GO
