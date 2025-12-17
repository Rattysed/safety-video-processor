# Safety video processor

## Fork of 
[Distributed image converter](https://github.com/Rattysed/distributed-image-converter)


## Установка и запуск

### Общие шаги
```bash
# Клонирование репозитория
git clone https://github.com/Rattysed/safety-video-processor.git
cd safety-video-processor
```

### Production запуск

```bash
# Создание файла конфигурации
cp .env.prod.example .env.prod
```

Настройте переменные в файле `.env.prod` в соответствии с вашими требованиями.

### Development запуск
```bash
# Создание файла конфигурации
cp .env.example .env
```

Настройте переменные в файле `.env` в соответствии с вашими требованиями.

```bash
# Запуск контейнеров
docker-compose up --build -d
```

### PROD запуск

```bash
# Создание файла конфигурации
cp .env.example .env
cp Dockerfile.cuda worker/Dockerfile
cp Dockerfile.cuda backend/Dockerfile
```


#### Полезные команды

```bash
# Создать миграции
docker-compose exec backend python manage.py makemigrations

# Просмотреть логи
docker-compose logs
```
