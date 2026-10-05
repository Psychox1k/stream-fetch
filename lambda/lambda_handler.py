import urllib.parse
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')


def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        content_type = response.get('ContentType', 'unknown')
        file_size = response.get('ContentLength', 0)

        logger.info(f"Successfully processed file: {key}")
        logger.info(f"Size: {file_size} bytes. Type: {content_type}")

        return {
            'statusCode': 200,
            'body': f'File {key} processed successfully'
        }
    except Exception as e:
        logger.error(f"Error processing file {key} from bucket {bucket}. Details: {str(e)}")
        raise e