import discord
import API_Keys as API
from discord.ext import commands
import MarketCheck

# Створюємо інстанцію бота
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Глобальні змінні
price_difference_filter: float = 10
tracked_item = "octavia_prime_set"
notified_orders = set()

@bot.event
async def on_ready():
    print(f'Бот підключений як {bot.user}')
    bot.loop.create_task(MarketCheck.check_prices_periodically(
        bot, API.CHANNEL_ID, tracked_item, price_difference_filter, notified_orders
    ))

@bot.command()
async def settings(ctx, *args):
    global price_difference_filter, tracked_item

    if len(args) == 0:
        # Вивести поточні налаштування
        await ctx.send(f"Поточний фільтр різниці: {price_difference_filter} пл, відстежуваний предмет: {tracked_item.replace('_', ' ')}.")
    elif len(args) == 1:
        try:
            new_filter_value = int(args[0])
            price_difference_filter = new_filter_value
            await ctx.send(f"Фільтр різниці встановлено на {price_difference_filter} пл.")
        except ValueError:
            await ctx.send("Помилка: Різниця повинна бути числовим значенням.")
    elif len(args) == 2:
        try:
            new_filter_value = int(args[0])
            new_item_name = args[1].replace(" ", "_").lower()
            if MarketCheck.validate_item_name(new_item_name):
                price_difference_filter = new_filter_value
                tracked_item = new_item_name
                await ctx.send(f"Фільтр різниці встановлено на {price_difference_filter} пл, відстежується предмет: {tracked_item.replace('_', ' ')}.")
            else:
                await ctx.send(f"Предмет `{new_item_name.replace('_', ' ')}` не знайдено.")
        except ValueError:
            await ctx.send("Помилка: Різниця повинна бути числовим значенням.")

@bot.command()
async def market_data(ctx):
    global tracked_item
    last_5_orders, average_price = await MarketCheck.get_warframe_market_data(tracked_item)
    
    if last_5_orders:
        stats = f"Останні 5 замовлень для {tracked_item.replace('_', ' ')}:\n"
        for order in last_5_orders:
            stats += (
                f" - {order['quantity']} шт | {order['platinum']} пл | "
                f"Користувач: {order['user']['ingame_name']} ({order['user']['region']})\n"
            )
        # Відправляємо повідомлення по частинам, якщо воно надто велике для одного повідомлення
        for i in range(0, len(stats), 2000):
            await ctx.send(stats[i:i+2000])
    else:
        await ctx.send(f"Не вдалося отримати дані для предмета `{tracked_item.replace('_', ' ')}`.")

bot.run(API.DISCORD_TOKEN)
