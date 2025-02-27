import main_nacional

def lambda_handler(event, context):
    print("Iniciando scraping de portais nacionais...")
    main_nacional.main()
    return {
        "statusCode": 200,
        "body": "Scraping nacional concluído!"
    }