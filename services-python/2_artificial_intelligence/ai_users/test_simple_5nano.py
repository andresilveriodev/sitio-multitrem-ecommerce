#!/usr/bin/env python3
import os
from openai import OpenAI
from dotenv import load_dotenv

# Carrega o .env
load_dotenv()

def test_financial_order_interpretation():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    resp = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": "Você interpreta ordens financeiras e responde em JSON: {ticker, operação, quantidade, preço, tipo_ordem}."},
            {"role": "user", "content": "Quero comprar PETR4 a 30 reais"}
        ],
        temperature=1
    )

    print("Resposta:", resp.choices[0].message.content)

def test_multiple_orders():
    orders = [
        "Comprar 100 ações da VALE3 por R$ 65,50",
        "Vender ITUB4 a mercado",
        "Quero vender 50 BBAS3 a R$ 45,00",
        "Compra MGLU3 stop loss em 15 reais"
    ]

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    for order in orders:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você interpreta ordens financeiras e responde em JSON: {ticker, operação, quantidade, preço, tipo_ordem}."},
                {"role": "user", "content": order}
            ],
            temperature=0.0
        )
        print(f"\nEntrada: {order}")
        print(f"Saída: {resp.choices[0].message.content}")

if __name__ == "__main__":
    test_financial_order_interpretation()
    test_multiple_orders()
