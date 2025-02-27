import main_local

def lambda_handler(event, context):
    print("Iniciando scraping de portais locais...")
    main_local.main()
    return {
        "statusCode": 200,
        "body": "Scraping local concluído!"
    }