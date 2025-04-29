# lambda/index.py
import json
import re  # 正規表現モジュールをインポート
import urllib.request
from botocore.exceptions import ClientError

# Lambda コンテキストからリージョンを抽出する関数
def extract_region_from_arn(arn):
    # ARN 形式: arn:aws:lambda:region:account-id:function:function-name
    match = re.search('arn:aws:lambda:([^:]+):', arn)
    if match:
        return match.group(1)
    return "us-east-1"  # デフォルト値

def lambda_handler(event, context):
    try:
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        print("Processing message:", message)

        # 会話履歴を使用
        messages = conversation_history.copy()
        
        # ユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })

        url = 'https://38da-34-147-8-7.ngrok-free.app/generate'
        data = {
            "prompt": message,
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }
        headers = {
            'Content-Type': 'application/json',
        }

        # レスポンスを解析
        req = urllib.request.Request(url, json.dumps(data).encode(), headers)
        with urllib.request.urlopen(req) as res:
            response_body = res.read()
            print("Raw response:", response_body)  # デバッグ用
            try:
                # バイト文字列をデコードしてJSONとして解析
                response_body = json.loads(response_body.decode('utf-8'))
                print("Parsed response:", response_body)  # デバッグ用
            except json.JSONDecodeError as e:
                print("JSON decode error:", str(e))
                raise Exception(f"Failed to parse response as JSON: {str(e)}")

        if not isinstance(response_body, dict):
            raise Exception(f"Unexpected response type: {type(response_body)}")
        if not response_body.get('generated_text'):
            raise Exception("No generated_text in response")
        
        # 応答の検証
        if not response_body.get('generated_text'):
            raise Exception("No response content from the model")
        
        # アシスタントの応答を取得
        assistant_response = response_body['generated_text']
        
        # アシスタントの応答を会話履歴に追加
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }
        
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }