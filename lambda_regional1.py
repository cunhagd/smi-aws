import main_regional1

def lambda_handler(event, context):
    print("Iniciando scraping de portais regionais (parte 1)...")
    main_regional1.main()
    return {
        "statusCode": 200,
        "body": "Scraping regional1 concluído!"
    }