import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse

app = FastAPI()

UPLOAD_DIRECTORY = "uploads"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True) 

html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Upload Satellite Images</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #121212; 
                color: #ffffff; 
                height: 100vh; 
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .container {
                max-width: 400px; 
                padding: 20px;
                background: #1e1e1e; 
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
                text-align: center; 
            }
            h1 {
                margin-bottom: 20px;
                font-size: 24px;
            }
            input[type="file"] {
                display: block;
                margin: 20px auto;
                border: 2px dashed #ffffff; 
                padding: 10px;
                background-color: #2e2e2e; 
                color: #ffffff;
            }
            button {
                padding: 10px 15px;
                background-color: #6200ea; 
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                transition: background-color 0.3s;
                font-size: 16px;
            }
            button:hover {
                background-color: #3700b3;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Upload Satellite Images</h1>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file" id="file" multiple required>
                <button type="submit">Upload</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
async def upload_form():
    return html


@app.post("/upload", response_class=HTMLResponse)
async def upload_file(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIRECTORY, file.filename)
    
    with open(file_location, "wb") as file_object:
        file_content = await file.read()
        file_object.write(file_content)

    return html
