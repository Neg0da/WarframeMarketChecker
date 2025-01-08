import requests
import aiohttp
import asyncio

def validate_item_name(item_name):
    url = f"https://api.warframe.market/v1/items/{item_name}"
    try:
        response = requests.get(url)
        return response.status_code == 200
    except Exception:
        return False

async def get_warframe_market_data(item_name):
    url = f"https://api.warframe.market/v1/items/{item_name}/orders"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                if 'payload' in data and 'orders' in data['payload']:
                    orders = data['payload']['orders']
                    sell_orders = [
                        order for order in orders if order['order_type'] == 'sell' and order['user']['status'] in ['online', 'ingame']
                    ]
                    sell_orders.sort(key=lambda x: x['creation_date'], reverse=True)
                    last_5_orders = sell_orders[:5]
                    average_price = sum(order['platinum'] for order in last_5_orders) / len(last_5_orders) if last_5_orders else 0
                    return last_5_orders, average_price
                return [], None
    except Exception as e:
        print(f"Помилка отримання даних з API: {e}")
        return [], None

async def check_prices_periodically(bot, channel_id, tracked_item, price_difference_filter, notified_orders):
    while True:
        try:
            last_5_orders, average_price = await get_warframe_market_data(tracked_item)
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
                        if channel:
                            message = (
                                f"Гравець {username} виставив замовлення на {platinum_price} пл, "
                                f"що дешевше на {price_difference_filter} пл від середнього.\n"
                                f"Щоб зв'язатися з гравцем, використайте:\n"
                                f"`/w {username} Hello! :blush: I want to buy: \"{tracked_item}\" for {platinum_price} :platinum: (warframe.market)`"
                            )
                            await channel.send(message)
                            notified_orders.add(order_id)
        except Exception as e:
            print(f"Помилка в check_prices_periodically: {e}")
        await asyncio.sleep(60)
