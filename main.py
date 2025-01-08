import discord
import API_Keys as API
import requests
import asyncio
from discord.ext import commands

# Створюємо інстанцію бота
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Глобальні змінні
price_difference_filter = 5  # Значення за замовчуванням для фільтра різниці від середнього
tracked_item = "octavia_prime_set"  # Значення за замовчуванням для предмету
notified_orders = set()  # Збереження ID замовлень, про які вже повідомляли

# Перевірка, чи існує предмет у Warframe Market
def validate_item_name(item_name):
    url = f"https://api.warframe.market/v1/items/{item_name}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception:
        return False

# Подія, яка спрацьовує, коли бот підключається до Discord
@bot.event
async def on_ready():
    print(f'Бот підключений як {bot.user}')
    bot.loop.create_task(check_prices_periodically())

# Функція для отримання даних з API Warframe Market
def get_warframe_market_data(item_name):
    url = f"https://api.warframe.market/v1/items/{item_name}/orders"
    try:
        response = requests.get(url)
        data = response.json()

        if 'payload' in data and 'orders' in data['payload']:
            orders = data['payload']['orders']
            sell_orders = [
                order for order in orders if order['order_type'] == 'sell' and order['user']['status'] in ['online', 'ingame']
            ]
            sell_orders.sort(key=lambda x: x['creation_date'], reverse=True)
            last_5_orders = sell_orders[:5]
            if last_5_orders:
                average_price = sum(order['platinum'] for order in last_5_orders) / len(last_5_orders)
            else:
                average_price = 0
            return last_5_orders, average_price
        else:
            return [], None
    except Exception as e:
        print(f"Помилка отримання даних з API: {e}")
        return [], None

# Функція для перевірки цін
async def check_prices_periodically():
    global price_difference_filter, tracked_item, notified_orders
    channel_id = API.CHANNEL_ID

    while True:
        try:
            last_5_orders, average_price = get_warframe_market_data(tracked_item)

            if average_price is not None:
                for order in last_5_orders:
                    order_id = order['id']
                    if (
                        order['platinum'] < average_price - price_difference_filter
                        and order_id not in notified_orders
                    ):
                        username = order['user']['ingame_name']
                        platinum_price = order['platinum']
                        channel = bot.get_channel(channel_id)

                        if channel is not None:
                            message = (
                                f"Гравець {username} виставив замовлення на {platinum_price} пл, "
                                f"що дешевше на {price_difference_filter} пл від середнього.\n"
                                f"Щоб зв'язатися з гравцем, використайте:\n"
                                f"`/w {username} Hello! :blush: I want to buy: \"{tracked_item}\" for {platinum_price} :platinum: :inlove: (warframe.market)`"
                            )
                            await channel.send(message)
                            notified_orders.add(order_id)
                        else:
                            print(f"Помилка: Канал з ID {channel_id} не знайдено.")
                            break

        except Exception as e:
            print(f"Помилка в check_prices_periodically: {e}")

        await asyncio.sleep(60)

# Подія, яка спрацьовує при отриманні повідомлення
@bot.event
async def on_message(message):
    global price_difference_filter, tracked_item

    if bot.user in message.mentions:
        content = message.content.split()
        if len(content) > 1:
            try:
                # Якщо користувач передав 2 параметри (різниця і назва предмету)
                if len(content) == 3:
                    new_filter_value = int(content[1])
                    new_item_name = content[2].replace(" ", "_").lower()  # Перетворюємо назву в формат API

                    # Перевіряємо, чи існує предмет
                    if validate_item_name(new_item_name):
                        price_difference_filter = new_filter_value
                        tracked_item = new_item_name
                        await message.channel.send(
                            f"Фільтр різниці встановлено на {price_difference_filter} пл. "
                            f"Відстежується предмет: {tracked_item}."
                        )
                    else:
                        await message.channel.send(
                            f"Предмет `{new_item_name.replace('_', ' ')}` не знайдено. "
                            f"Будь ласка, перевірте правильність назви і спробуйте ще раз."
                        )
                # Якщо переданий лише один параметр (різниця)
                elif len(content) == 2:
                    new_filter_value = int(content[1])
                    price_difference_filter = new_filter_value
                    await message.channel.send(f"Фільтр різниці встановлено на {price_difference_filter} пл.")
            except ValueError:
                await message.channel.send("Помилка: Різниця повинна бути числовим значенням. Спробуйте ще раз.")
        else:
            last_5_orders, average_price = get_warframe_market_data(tracked_item)
            if last_5_orders and average_price is not None:
                stats = f"Середня ціна останніх 5 замовлень для {tracked_item.replace('_', ' ')}: {average_price:.2f} пл\n"
                for order in last_5_orders:
                    stats += (
                        f" - {order['quantity']} шт | {order['platinum']} пл | "
                        f"Користувач: {order['user']['ingame_name']} ({order['user']['region']})\n"
                    )
                for i in range(0, len(stats), 2000):
                    await message.channel.send(stats[i:i+2000])

    await bot.process_commands(message)

# Запуск бота
bot.run(API.DISCORD_TOKEN)
