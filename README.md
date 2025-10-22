# 🧠 String Analyzer API

A Django REST Framework API for analyzing strings — detecting palindromes, counting words, filtering by natural language queries, and more.  
This project was built as part of an API engineering task to demonstrate backend design, validation, and response structuring.

---

## 🚀 Features

- Analyze and store string properties (length, palindrome, word count, etc.)
- Retrieve or delete specific strings by value or hash
- Filter strings with query parameters
- Use natural language filters (e.g., “show palindromes longer than 5 letters”)
- Error handling with clear status codes and messages
  - `400 Bad Request` – Invalid parameters
  - `409 Conflict` – String already exists
  - `422 Unprocessable Entity` – Invalid data type for `value`

---

## ⚙️ Project Setup

###  1. Clone the Repository
```bash
git clone [the repo](https://github.com/success-10/hng-string-analyzer.git)
cd stage_1
```

---
### 2. Create and Activate a Virtual Environment
```bash
# For Windowspip install -r requirements.txt
```
If you don’t have a requirements.txt file yet, you can generate one:
```bash
pip freeze > requirements.txt
```
### 3. Dependencies
Main dependencies used in this project:

Package	Description
1. Django:	The web framework used
2. Django REST Framework (DRF):	For building the RESTful API
3. django-filter:	For advanced query filtering
4. mysqlclient:	MySQL database connector
5. python-dotenv:	To load environment variables from .env file

### 4. Environment Variables
Create a .env file in your project root and include:
```bash
SECRET_KEY=your_secret_key_here
DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=your-db-name
DB_USER=user-name
DB_PASSWORD=password
DB_HOST=127.0.0.1
DB_PORT=3306
```
## 5. Running the API Locally
### 1. Apply Migrations
```bash

python manage.py makemigrations
python manage.py migrate
```
### 2. Run the Development Server
```bash

python manage.py runserver
```
Visit your API locally at http://127.0.0.1:8000/

### 3. Running Tests
The project includes automated tests for all endpoints.

To run them:

```bash

python manage.py test
```
## 6. Example Endpoints
1. POST /strings/
Analyze and save a string.

Request:
```bash
{
  "value": "madam"
}
```
Successful Response (201):
```bash
{
  "id": "af9b2d3...",
  "value": "madam",
  "is_palindrome": true,
  "length": 5,
  "word_count": 1
}
```
Invalid Data Type (422):
```bash
{
  "detail": "Invalid data type for 'value' (must be string)"
}
```
2. GET /strings/
List all analyzed strings or filter them.

Example:

```bash

GET /strings?is_palindrome=true&min_length=4
```
3. GET /strings/{string_value}
Retrieve details of a specific string by its value or hash.

4. DELETE /strings/{string_value}
Delete an analyzed string.

5. GET /strings/filter-by-natural-language?query=palindromes longer than 4
Filter using a natural language query.

