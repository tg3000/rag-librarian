from sentence_transformers import SentenceTransformer
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

import logging

class EmbeddingClass(EmbeddingFunction):
    def __init__(self):
        self.model = SentenceTransformer("intfloat/multilingual-e5-base", device="cpu")
    def __call__(self, texts: list[str]) -> list[list[float]]:
        with torch.no_grad():
            return self.model.encode(texts).tolist()

class Model():
    def __init__(self, database_folder, system_prompt=""):
        logging.basicConfig(filename="log.log", filemode="w", format="%(asctime)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.system_prompt = system_prompt
        self.model_id = "mistralai/Mistral-7B-Instruct-v0.3"
        self.client = chromadb.PersistentClient(path=database_folder)
        self.collection = self.client.get_or_create_collection("historical_docs", embedding_function=EmbeddingClass())
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_id, load_in_4bit=True, device_map="auto", low_cpu_mem_usage=True)
        self.conversations = []

    def start_new_conv(self) -> int:
        pos = len(self.conversations)
        self.conversations.append([{"role": "system", "content": self.system_prompt}])
        return len(self.conversations)-1

    def prompt(self, prompt_text, chat_idx) -> str:
        self.logger.info("Prompt: " + prompt_text)

        contexts = self.collection.query(query_texts=[prompt_text], n_results=2)["documents"][0]
        
        context = ""
        log_count = 0
        for text in contexts:
            log_count += 1
            self.logger.info("Context " + str(log_count) + ": " + text)
            context += text
        conversation = self.conversations[chat_idx].copy()
        conversation.append({"role": "user", "content": prompt_text + "\nHere you have context from scientific documents, but do not mention them in your answer and only write things in your answer that you are sure about. Write concisely, do not repeat yourself, and answer only the question, even if you get more context: " + context})
        inputs = self.tokenizer.apply_chat_template(
                    conversation,
                    add_generation_prompt=True,
                    return_dict=True,
                    return_tensors="pt",
        )
        inputs.to(self.model.device)
        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=1000, eos_token_id=self.tokenizer.eos_token_id)
        prompt_length = inputs["input_ids"].shape[1]  # number of tokens in the prompt
        generated_tokens = outputs[0][prompt_length:]
        answer = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        self.conversations[chat_idx].append({"role": "user", "content": prompt_text})
        self.conversations[chat_idx].append({"role": "assistant", "content": answer})
        outputs = outputs.cpu()
        del inputs
        del outputs
        torch.cuda.empty_cache()
        self.logger.info("Answer: " + answer)
        return answer
    
    def quick_prompt(self, prompt_text):
        chat_idx = self.start_new_conv()
        answer = self.prompt(prompt_text, chat_idx)
        self.conversations = self.conversations[:-1]
        return answer