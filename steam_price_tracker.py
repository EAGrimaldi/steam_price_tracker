import requests
import json
import warnings
import datetime
import os
from typing import Tuple

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

class SteamPriceTracker:
    base_url = "https://www.steamwebapi.com/steam/api/"
    api_key = "PLACEHOLDER_KEY"
    steam_id = "PLACEHOLDER_ID"
    COLORS = {
        'white': '\u001b[37m',
        'pale blue': '\u001b[34;1m',
        'blue': '\u001b[34m',
        'purple': '\u001b[35m',
        'pink': '\u001b[35;1m',
        'red': '\u001b[31m',
        'orange': '\u001b[31;1m',
        'yellow': '\u001b[33;1m',
        'green': '\u001b[32m',
        'reset': '\u001b[0m',
    }
    rarity2color = {
        'consumer grade': COLORS['white'],
        'industrial grade': COLORS['pale blue'],
        'mil-spec grade': COLORS['blue'],
        'restricted': COLORS['purple'],
        'classified': COLORS['pink'],
        'covert': COLORS['red'],
        'rare special': COLORS['yellow'],
        'contraband': COLORS['orange'],
    }
    def __init__(self, mode: str='load', private_info_file: str=None, private_collection_file: str=None) -> None:
        if private_info_file is None:
            private_info_file = os.path.join(__location__, 'private_info.txt')
        with open(private_info_file, 'r') as file:
            self.api_key = file.readline().strip()
            self.steam_id = file.readline().strip()
        self.private_collection_file = os.path.join(__location__, 'private_collection.json') if private_collection_file is None else private_collection_file
        mode = mode.lower().strip()
        mode2func = {
            'load': self.__load_collection__,
            'import': self.__import_inventory__,
        }
        if mode not in mode2func:
            raise KeyError("Invalid mode selected. Valid modes are 'load' and 'import'")
        mode2func[mode]()            
    def __import_inventory__(self) -> None:
        response = requests.get(f'{self.base_url}inventory', params={
            'key': self.api_key,
            'steam_id': self.steam_id,
            'game': 'csgo',
        })
        response.raise_for_status()
        self.collection_json = response.json()
        self.__save_collection__()
    def __load_collection__(self) -> None:
        with open(self.private_collection_file, 'r') as file:
            self.collection_json = json.load(file)
    def __save_collection__(self) -> None:
        with open(self.private_collection_file, 'w') as file:
            json.dump(self.collection_json, file, indent=4)
    def display_collection(self, update_price: bool=False) -> None:
        print(''.ljust(128, '-'))
        print(f"{'Item'.ljust(16)} | {'Skin'.ljust(16)} | Wear | {'Buy Price'.ljust(12)} | {'Buy Date'.ljust(12)} | {'Check Price'.ljust(12)} | {'Check Date'.ljust(12)} | {'Price Change'.ljust(12)} | % Change")
        print(''.ljust(128, '-'))
        buy_price_total_value = 0
        check_price_total_value = 0
        for item in self.collection_json:
            for tag in item['tags']:
                if tag['category'] == 'Weapon':
                    # TODO add functionality for Knives, Gloves, Agents, and Music Kits
                    # need someone to supply an example inventory that isn't *hundreds* of items (API tokens aren't free!)
                    buy_price_value, check_price_value = self.display_item(item, update_price)
                    buy_price_total_value += buy_price_value
                    check_price_total_value += check_price_value
                    break
        print(''.ljust(128, '-'))
        total_price_change = check_price_total_value - buy_price_total_value
        total_percent_change = 100 * total_price_change / buy_price_total_value
        color = self.COLORS['green'] if total_percent_change > 1 else ( self.COLORS['red'] if total_percent_change < -1 else self.COLORS['reset'])
        check_price_total = f'${check_price_total_value:.2f}USD'.rjust(12)
        buy_price_total = f'${buy_price_total_value:.2f}USD'.rjust(12)
        total_price_change = f'-${-1*total_price_change:.2f}USD'.rjust(12) if total_price_change < 0 else f'${total_price_change:.2f}USD'.rjust(12)
        total_percent_change = f'{total_percent_change:.2f}%'.rjust(8)
        print(f"{'total'.ljust(42)} | {buy_price_total} | {12*' '} | {check_price_total} | {12*' '} | {color}{total_price_change} | {total_percent_change}{self.COLORS['reset']}")
        print(''.ljust(128, '-'))
    def display_item(self, item:dict, update_price: bool=False) -> None:
        name = self.__format_name__(item)
        prices, buy_price_value, check_price_value = self.__format_prices__(item, update_price)
        print(f"{name} | {prices}")
        return (buy_price_value, check_price_value)
    def __format_name__(self, item: dict) -> str:
        rarity_color = self.rarity2color[item['rarity']]
        weapon, skin, wear = item['itemtype'], item['itemname'], item['wear']
        weapon = weapon.strip().ljust(16)
        skin = skin.strip()
        skin = skin.ljust(16) if len(skin) < 16 else skin[0:15] + '.'
        wear = wear[0] + '.' + wear[1] + '.'
        return f"{rarity_color}{weapon} | {skin} | {wear}{self.COLORS['reset']}"
    def __format_prices__(self, item: dict, update_price: bool = False) -> Tuple[str, float, float]:
        current_date = datetime.date.today()
        check_date = item['priceupdatedat']['date'][0:11].split('-')
        check_date = datetime.date(int(check_date[0]), int(check_date[1]), int(check_date[2]))
        out_of_date = True if (current_date-check_date).days > 28 else False
        check_date = item['priceupdatedat']['date'][0:11].ljust(12)
        if update_price or out_of_date:
            # TODO implement price update request
            warnings.warn('Your latest check price is severely out of date!')
            warnings.warn('Automatic out-of-date price update is not yet implemented...')
        check_price_value = item['pricelatest']
        if 'my_buy_date' in item:
            if 'my_buy_price' not in item:
                # TODO implement price history request
                warnings.warn('You have a buy date but no buy price.')
                warnings.warn('Price history request for automatic buy price estimation not yet implemented...')
            buy_date = item['my_buy_date'].ljust(12)
        else:
            buy_date = 'idk'.ljust(12)
        if 'my_buy_price' in item:
            buy_price_value = item['my_buy_price']
            price_change = check_price_value - buy_price_value
            percent_change = 100 * price_change / buy_price_value
            change_color = self.COLORS['green'] if percent_change > 1 else ( self.COLORS['red'] if percent_change < -1 else self.COLORS['reset'])
            buy_price = f'${buy_price_value:.2f}USD'.rjust(12)
            price_change = f'-${-1*price_change:.2f}USD'.rjust(12) if price_change < 0 else f'${price_change:.2f}USD'.rjust(12)
            percent_change = f'{percent_change:.2f}%'.rjust(8)
        else:
            buy_price = 'idk'.rjust(12)
            price_change = 'idk'.rjust(12)
            percent_change = 'idk'.rjust(8)
        check_price = f'${check_price_value:.2f}USD'.rjust(12)
        return (
            f"{buy_price} | {buy_date} | {check_price} | {check_date} | {change_color}{price_change} | {percent_change}{self.COLORS['reset']}",
            buy_price_value,
            check_price_value,
        )


if __name__ == "__main__":
    tracker = SteamPriceTracker(mode='load')
    tracker.display_collection()
