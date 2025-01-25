import openai
import anthropic
import google.generativeai as genai
# from utils import set_openai_api_key, set_gemini_api_key
from sentence_transformers import SentenceTransformer
from .perturb import Perturbation  # Import your perturbation functions from perturb.py
import requests
import spacy
import numpy as np 
# Initialize the sentence transformer model for similarity evaluation
# Initialize the sentence transformer model for similarity evaluation
similarity_model = SentenceTransformer("all-mpnet-base-v2")
url = "http://127.0.0.1:8000/v1/chat/completions" 

def evaluate_response(text1, text2, model):
    """
    Evaluate the response using the SentenceTransformer model.
    
    Parameters:
    text1 (str): The first text to compare.
    text2 (str): The second text to compare.
    model (SentenceTransformer): The model to use for generating embeddings.
    
    Returns:
    float: The similarity score between the two texts.
    """
    emb_a = model.encode([text1])
    emb_b = model.encode([text2])
    similarities = model.similarity(emb_a, emb_b)
    return similarities.item()

class PromptCompletion:
    def __init__(self, 
                 model_provider="openai",  # Can be 'openai', 'gemini', 'claude', or 'llama'
                 model="gpt-3.5-turbo",     
                 system_content="""You will act as a Question Answering model.""",
                 temperature=0, 
                 top_p=0, 
                 max_tokens=100,
                 api_key=None,
                 stream=False,
                 llama_url=url):
        """
        Initialize the PromptCompletion class with default parameters.

        Parameters:
        model_provider (str): The provider to use ('openai', 'gemini', 'claude', or 'llama').
        model (str): The model to use for generating responses.
        system_content (str): The system message that sets the context and format for the completions.
        temperature (float): Sampling temperature for the model.
        top_p (float): Nucleus sampling parameter.
        max_tokens (int): Maximum number of tokens in the response.
        api_key (str): The API key to use for the provider, if required.
        stream (bool): Whether to stream responses (Llama only).
        llama_url (str): The URL for the Llama model if using LMStudio.
        """
        self.model_provider = model_provider
        self.model = model
        self.system_content = system_content
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.stream = stream
        self.llama_url = llama_url

        if self.model_provider == "openai":
            # Set the OpenAI API key using the utility function
            if api_key:
                openai.api_key = self.api_key
            else:
                raise ValueError("OpenAI API key is required.")  

        elif self.model_provider == "claude":
            if not api_key:
                raise ValueError("Claude API key is required.")
            self.client = anthropic.Anthropic(api_key=api_key)  # Initialize the Claude client

        elif self.model_provider == "gemini":
            if not api_key:
                raise ValueError("Gemini API key is required.")
            genai.configure(api_key=api_key)  # Configure the Gemini API with the provided key

            # # Configure generation settings for Gemini
            # self.generation_config = {
            #     "temperature": self.temperature,
            #     "top_p": self.top_p,
            #     "max_output_tokens": self.max_tokens,
            #     "response_mime_type": "text/plain",
            # }
            # self.model_name = model  # Gemini model name (e.g., 'gemini-1.5-pro')

        elif self.model_provider == "llama":
            # No special API key needed for llama, but make sure the Llama server is running.
            if not llama_url:
                raise ValueError("Llama URL is required.")

        else:
            raise ValueError(f"Unknown model provider: {self.model_provider}")

    def generate_completion(self, prompt, batch=False, chain_of_thought=False):
        """
        Generate a completion for a given prompt using the set model and provider.
        
        Parameters:
        prompt (str): The input prompt for generating completion.
        batch (bool): Whether to send multiple prompts in a batch (for Claude).
        chain_of_thought (bool): Whether to generate a Chain of Thought (CoT) response.

        Returns:
        str: The completion text.
        """
        # Add Chain of Thought prompt modification
        if chain_of_thought:
            self.system_content = """You will act as a Question Answering model. You are prohibited to say anything. 

            Example #1:
            [Prompt] Q: Yes or no: Would a pear sink in water? 
            [Answer that you think] A: The density of a pear is about 0.6 g/cm^3, which is less than water. Thus, a pear would float. So the answer is no.

            [Answer that you must provide to me]So the answer is no.

            Example #2:
            [Prompt]Q: How many keystrokes are needed to type the numbers from 1 to 500? Answer Choices: (a) 1156 (b) 1392 (c) 1480 (d) 1562 (e) 1788
            [Answer that you think]A: The answer is B.

            [Answer that you must provide to me]The answer is B.
            
            Example #3
            [Prompt]Q: The cafeteria has 23 apples. If they used 20 to make lunch and bought 6 more.How many apples do they have?
            [Answer that you think]A: The cafeteria started with 23 apples, used 20 for lunch, and bought 6 more. So, they have 9 apples left.

            [Answer that you must provide to me]They have 9 apples left
            """

        if self.model_provider == "openai":
            """
            Generate a completion using OpenAI models.
            """
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_content},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens
            )
            response_content = response.choices[0].message['content'].strip()
            return response_content

        elif self.model_provider == "claude":
            """
            Generate a completion using Claude's Messages API.
            """
            formatted_prompt = f"\n\nHuman: {prompt}\n\nAssistant:"
            response = self.client.completions.create(
                model=self.model,
                max_tokens_to_sample=self.max_tokens,
                temperature=self.temperature,
                prompt=formatted_prompt
            )
            return response.completion

        elif self.model_provider == "gemini":
            """
            Generate a completion using Gemini's API.
            """
            model = genai.GenerativeModel(
                model_name=self.model,
                system_instruction=self.system_content)
            response = model.generate_content(prompt)
            return response.text
            # # Start a chat session with history and send the input prompt
            # model = genai.GenerativeModel(
            #     model_name=self.model_name,
            #     generation_config=self.generation_config,
            # )
            # chat_session = model.start_chat(
            #     history=[
            #         {
            #             "role": [self.system_content],
            #             "parts": [prompt]
            #         }
            #     ]
            # )
            # response = chat_session.send_message(prompt)
            # return response.text

        elif self.model_provider == "llama":
            """
            Generate a completion using a Llama model hosted on LMStudio.
            """
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_content},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": self.stream
            }

            response = requests.post(self.llama_url, json=data)

            if response.status_code == 200:
                # Extract the assistant's response content
                assistant_response = response.json()['choices'][0]['message']['content']
                return assistant_response
            else:
                return (f"Failed with status code {response.status_code}: {response.text}")

        else:
            raise ValueError(f"Model provider {self.model_provider} is not supported.")
class Test:
    def __init__(self, name, prompt, expected_result, description=None,
                 perturb_method=None, perturb_text=None, capability=None,
                 pass_condition="increase", test_type=None):
        self.name = name
        self.description = description
        self.prompt = prompt
        self.expected_result = expected_result
        self.perturb_method = perturb_method
        self.perturb_text = perturb_text
        self.capability = capability
        self.pass_condition = pass_condition
        self.test_type = test_type  
        self.original_response = None
        self.perturb_response = None
        self.score_original = None
        self.score_perturb = None
        self.completion_model = None

    def run(self, completion_model: PromptCompletion):
        self.completion_model = completion_model
        self.original_response = self.get_response(self.prompt)
        # if self.perturb_method:
        #     self.perturb_text = self.perturb_method(self.prompt)
        self.perturb_response = self.get_response(self.perturb_text)

        if self.original_response:
            self.score_original = self.evaluate(similarity_model, self.original_response)
        if self.perturb_response:
            self.score_perturb = self.evaluate(similarity_model, self.perturb_response)

    def get_response(self, text):
        if not text:
            return None
        return self.completion_model.generate_completion(text)

    def evaluate(self, model, response):
        if response is None:
            return None
        return evaluate_response(response, self.expected_result, model)

    def summarize(self):
        fail = False
        # Temporal Case = score decrease -> pass
        # if self.perturb_method == "temporal":
        #     self.pass_condition == "decrease"

        if self.score_original is not None and self.score_perturb is not None:
            if self.pass_condition == "decrease":
                if self.score_perturb >= self.score_original:
                    fail = True
            elif self.pass_condition == "increase":
                if self.score_perturb < self.score_original:
                    fail = True
                if self.score_original < 0.7:
                    fail = True
        return {
            'name': self.name,
            'description': self.description,
            'test_type': self.test_type,  
            'prompt': self.prompt,
            'expected_result': self.expected_result,
            'perturb_text': self.perturb_text,
            'pass_condition': self.pass_condition,
            'capability': self.capability,
            'response_original': self.original_response,
            'response_perturb': self.perturb_response,
            'score_original': self.score_original,
            'score_perturb': self.score_perturb,
            'fail': fail
        }
