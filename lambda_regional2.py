import main_regional2

def lambda_handler(event, context):
    print("Iniciando scraping de portais regionais (parte 2)...")
    main_regional2.main()
    return {
        "statusCode": 200,
        "body": "Scraping regional2 concluído!"
    }