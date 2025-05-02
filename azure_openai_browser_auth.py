import os
from openai import AzureOpenAI
from azure.identity import InteractiveBrowserCredential
from dotenv import load_dotenv
from config import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION

# Load environment variables if you have a .env file
load_dotenv()

def main():
    print("Starting Azure OpenAI Test with browser authentication...")
    
    try:
        # Authenticate using browser-based authentication
        credential = InteractiveBrowserCredential()
        
        # Get the token
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        
        # Create the Azure OpenAI client with the token
        client = AzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_ad_token=token.token
        )
          # Send a test request to Azure OpenAI
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,  # This is the deployment name
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello! What can you tell me about Azure OpenAI?"}
            ]
        )
        
        # Print the response
        print("\nResponse from Azure OpenAI:")
        print(response.choices[0].message.content)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
