# Vercel serverless handler
from main import app as application

# Vercel expects the app to be named 'app' or be in a variable called 'handler'
app = application
