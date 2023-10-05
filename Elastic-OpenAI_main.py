# elastic open AI integration elastic reads multiline xml from an url response
# built for a customer to insert documents into elastic directly from an Url scrape
# Satish Bomma
# 05.03.2023

# import statments

import os
import logging
import streamlit as st
import openai
from elasticsearch import Elasticsearch
import requests
from datetime import datetime
import json
import yaml
import tiktoken

now = datetime.now();
dt_string = now.strftime("%m%d%Y %H:%M:%S")


# Elastic Seaerch Connect Parametres
def es_connect(cid, user, passwd):
    es = Elasticsearch(cloud_id=cid, http_auth=(user, passwd))
    return es

# Search Queries to be executed
def search(query_txt, username, password, cloud_id, index_name):

    es = es_connect(cloud_id, username, password)
    query = {
        "text_expansion": {
            "ml.inference.body_content_expanded.predicted_value": {
                "model_text": query_txt,
                "model_id": ".elser_model_1",
                "boost": 3
            }
        }
    }
    index = index_name
    fields = ["body_content", "url", "title"]

    resp = es.search(index=index_name, fields=fields, query=query, size=1, source=False)
    body = resp['hits']['hits'][0]['fields']['body_content'][0]
    url = resp['hits']['hits'][0]['fields']['url'][0]
    return body, url


def search_elser(query_txt, username, password, cloud_id, index_name):

    es = es_connect(cloud_id, username, password)
    query = {
        "text_expansion": {
            "ml.inference.body_content_expanded.predicted_value": {
                "model_text": query_txt,
                "model_id": ".elser_model_1",
                "boost": 3
            }
        }
    }
    index = index_name
    fields = ["body_content", "url", "title"]
    resp = es.search(index=index_name, fields=fields, query=query, size=10, source=False)
    hit = resp['hits']['hits']
    return hit

def search_bm25(query_txt, username, password, cloud_id, index_name):

    es = es_connect(cloud_id, username, password)
    query = {
        "match": {
            "body_content": query_txt
            }
        }
    index = index_name
    fields = ["body_content", "url", "title"]
    resp = es.search(index=index_name, fields=fields, query=query, size=10, source=False)
    hit = resp['hits']['hits']
    return hit


def truncate_text(text, max_tokens):
    tokens = text.split()
    if len(tokens) <= max_tokens:
        return text, len(tokens)

    return ' '.join(tokens[:max_tokens]), len(tokens)


# Integration with OpenAI 3.5

def encoding_token_count(string: str, encoding_model: str) -> int:
    encoding = tiktoken.encoding_for_model(encoding_model)
    return len(encoding.encode(string))


def chat_gpt(prompt, model="gpt-3.5-turbo", max_tokens=1024, max_context_tokens=4000, safety_margin=5):
    # Truncate the prompt content to fit within the model's context length
    truncated_prompt, word_count = truncate_text(prompt, max_context_tokens - max_tokens - safety_margin)
    openai_token_count = encoding_token_count(prompt, model)
    #print(f"word_count = {word_count}, openai_token_count = {openai_token_count}")

    response = openai.ChatCompletion.create(model=model,
                                            messages=[
                                                {"role": "system", "content": "You are a helpful assistant."},
                                                {"role": "user", "content": truncated_prompt}])

    return response["choices"][0]["message"]["content"], word_count, openai_token_count


def listToString(s):
    # initialize an empty string
    str1 = " "

    # return string
    return (str1.join(s))


# Main Starts here
def main(ivalue=None):
    cloud_id = ""
    password = ""
    username = ""
    openai.api_key = ""
    index_name = "search-elastic-docs"

    st.title("Compare three ways to search with Elsasticsearch")
    with st.form("chat_form"):
        query = st.text_input("Search: ")
        submit_button = st.form_submit_button("Send")
    negResponse = "Not able to find the requested search term"

    if submit_button:

        gpt_col, elser_col, bm25col = st.columns(3)
        gpt_col.subheader("Open AI Output")
        elser_col.subheader("ESRE Search")
        bm25col.subheader("Keyword Search")

        resp, url = search(query, username, password, cloud_id, index_name)
        prompt = f"Answer this question: {query}\nUsing only the information from Elastic.co Website: {resp}\nIf the answer is not contained in the supplied doc reply '{negResponse}' and nothing else"
        answer, word_count, openai_token_count = chat_gpt(prompt)
        #print("prompt>", prompt)
        #print("resp>", resp)
        #print("url>", url)
        #print("answer>", answer)

        if negResponse in answer:
            gpt_col.write(f"ChatGPT: {answer.strip()}")
        else:
            gpt_col.write(f"ChatGPT: {answer.strip()}\n\nArticle-url: {url}")

        try:
            hit = search_elser(query, username, password, cloud_id, index_name)
            hit_str = json.dumps(hit)
            hit_dict = json.loads(hit_str)
            #print(hit_dict)

            for dict in hit_dict:
                msg1= listToString(dict['fields']['title'])
                msg2= listToString(dict['fields']['url'])
                elser_col.write(f"{msg1}\n{msg2}")

        except Exception as error:
              elser_col.write("nothing returned", error)
              print(error)

        try:
            hit = search_bm25(query, username, password, cloud_id, index_name)
            hit_str = json.dumps(hit)
            hit_dict = json.loads(hit_str)
            #print(hit_dict)

            for dict in hit_dict:
                msg1= listToString(dict['fields']['title'])
                msg2= listToString(dict['fields']['url'])
                bm25col.write(f"{msg1} \n {msg2}")

        except Exception as error:
            elser_col.write("nothing returned", error)
            print(error)


def click_button_ok():
    print("do nothing")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    st.set_page_config(layout="wide")

    #print("Username>", Username)
    #print("Passcode>", Passcode)
    #print("CloudID>", CloudID)
    #print("OpenAIAPIkey>", OpenAIAPIkey)
    def add_bg_from_url():
        st.markdown(
            f"""
             <style>
             .stApp {{
                 #background-image: url("https://cdn.pixabay.com/photo/2019/04/24/11/27/flowers-4151900_960_720.jpg");
                 #background-image: calum-lewis-vA1L1jRTM70-unsplash.jpg 
                 background-attachment: fixed;
                 background-size: cover
             }}
             </style>
             """,
            unsafe_allow_html=True
        )


    add_bg_from_url()

    main()
