import discord
import API_Keys as API
from discord.ext import commands
import MarketCheck

# Створюємо інстанцію бота
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Глобальні змінні
price_difference_filter : float = 10
tracked_item = "octavia_prime_set"
notified_orders = set()

@bot.event
async def on_ready():
    print(f'Бот підключений як {bot.user}')
    bot.loop.create_task(MarketCheck.check_prices_periodically(
        bot, API.CHANNEL_ID, tracked_item, price_difference_filter, notified_orders
    ))

@bot.event
async def on_message(message):
    global price_difference_filter, tracked_item
    if bot.user in message.mentions:
        content = message.content.split()
        if len(content) > 1:
            try:
                if len(content) == 3:
                    new_filter_value = int(content[1])
                    new_item_name = content[2].replace(" ", "_").lower()
                    if MarketCheck.validate_item_name(new_item_name):
                        price_difference_filter = new_filter_value
                        tracked_item = new_item_name
                        await message.channel.send(
                            f"Фільтр різниці встановлено на {price_difference_filter} пл. "
                            f"Відстежується предмет: {tracked_item}."
                        )
                    else:
                        await message.channel.send(
                            f"Предмет `{new_item_name.replace('_', ' ')}` не знайдено."
                        )
                elif len(content) == 2:
                    new_filter_value = int(content[1])
                    price_difference_filter = new_filter_value
                    await message.channel.send(f"Фільтр різниці встановлено на {price_difference_filter} пл.")
            except ValueError:
                await message.channel.send("Помилка: Різниця повинна бути числовим значенням.")
        else:
            last_5_orders, average_price = await MarketCheck.get_warframe_market_data(tracked_item)
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

bot.run(API.DISCORD_TOKEN)
