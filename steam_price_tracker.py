import requests
import json
import warnings
import datetime

class SteamPriceTracker:
    base_url = "https://www.steamwebapi.com/steam/api/"
    api_key = "PLACEHOLDER_KEY"
    steam_id = "PLACEHOLDER_ID"
    rarity2color = {
        'consumer grade': '\u001b[37m', # white
        'industrial grade': '\u001b[34;1m', # pale plue ("bright blue")
        'mil-spec grade': '\u001b[34m', # blue
        'restricted': '\u001b[35m', # purple ("magenta")
        'classified': '\u001b[35;1m', # pink ("bright magenta")
        'covert': '\u001b[31m', # red
        'rare special': '\u001b[33;1m', # yellow
        'contraband': '\u001b[31;1m', # orange ("bright red")
    }
    def __init__(self, mode: str='load') -> None:
        with open('private_info.txt', 'r') as file:
            self.api_key = file.readline().strip()
            self.steam_id = file.readline().strip()
        mode2func = {
            'load': self.__load_collection__,
            'import': self.__import_inventory__,
        }
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
        with open('private_collection.json', 'r') as file:
            self.collection_json = json.load(file)
    def __save_collection__(self) -> None:
        with open('private_collection.json', 'w') as file:
            json.dump(self.collection_json, file, indent=4)
    def display_collection(self, update_price: bool=False) -> None:
        print(''.ljust(128, '-'))
        print(f"{'Item'.ljust(16)} | {'Skin'.ljust(16)} | Wear | {'Buy Price'.ljust(12)} | {'Buy Date'.ljust(12)} | {'Check Price'.ljust(12)} | {'Check Date'.ljust(12)} | {'Price Change'.ljust(12)} | % Change")
        print(''.ljust(128, '-'))
        for item in self.collection_json:
            for tag in item['tags']:
                if tag['category'] == 'Weapon':
                    # TODO add functionality for Knives, Gloves, Agents, and Music Kits
                    self.display_item(item, update_price)
                    break
        print(''.ljust(128, '-'))
        # TODO implement running totals
        warnings.warn('Running total value of inventory not yet implemented...')
        check_price_total = 1
        buy_price_total = 1
        total_price_change = check_price_total - buy_price_total
        total_percent_change = 100 * total_price_change / buy_price_total
        color = '\u001b[32m' if total_percent_change > 1 else ( '\u001b[31m' if total_percent_change < -1 else '\u001b[0m')
        reset = '\u001b[0m'
        check_price_total = f'${check_price_total}USD'.rjust(12)
        buy_price_total = f'${buy_price_total}USD'.rjust(12)
        total_price_change = f'-${-1*total_price_change:.2f}USD'.rjust(12) if total_price_change < 0 else f'${total_price_change:.2f}USD'.rjust(12)
        total_percent_change = f'{total_percent_change}%'.rjust(8)
        print(f"{'total'.ljust(42)} | {check_price_total} | {12*' '} | {buy_price_total} | {12*' '} | {color}{total_price_change} | {total_percent_change}{reset}")
        print(''.ljust(128, '-'))
    def display_item(self, item:dict, update_price: bool=False) -> None:
        name = self.__parse_name__(item)
        price_check = self.__price_check__(item, update_price)
        print(f"{name} | {price_check}")
    def __parse_name__(self, item: dict) -> str:
        rarity_color = self.rarity2color[item['rarity']]
        reset = '\u001b[0m'
        weapon, skin, wear = item['itemtype'], item['itemname'], item['wear']
        weapon = weapon.strip().ljust(16)
        skin = skin.strip()
        skin = skin.ljust(16) if len(skin) < 16 else skin[0:15] + '.'
        wear = wear[0] + '.' + wear[1] + '.'
        return f'{rarity_color}{weapon} | {skin} | {wear}{reset}'
    def __price_check__(self, item: dict, update_price: bool = False) -> str:
        change_color = '\u001b[0m'
        reset = '\u001b[0m'
        current_date = datetime.date.today()
        check_date = item['priceupdatedat']['date'][0:11].split('-')
        check_date = datetime.date(int(check_date[0]), int(check_date[1]), int(check_date[2]))
        out_of_date = True if (current_date-check_date).days > 28 else False
        check_date = item['priceupdatedat']['date'][0:11].ljust(12)
        if update_price or out_of_date:
            # TODO implement price update request
            warnings.warn('Your latest check price is severely out of date!')
            warnings.warn('Automatic out-of-date price update is not yet implemented...')
        check_price = item['pricelatest']
        if 'my_buy_date' in item:
            if 'my_buy_price' not in item:
                # TODO implement price history request
                warnings.warn('You have a buy date but no buy price.\nPrice history request for automatic buy price estimation not yet implemented...')
            buy_date = item['my_buy_date'].ljust(12)
        else:
            buy_date = 'idk'.ljust(12)
        if 'my_buy_price' in item:
            buy_price = item['my_buy_price']
            price_change = check_price - buy_price
            percent_change = 100 * price_change / buy_price
            change_color = '\u001b[32m' if percent_change > 1 else ( '\u001b[31m' if percent_change < -1 else '\u001b[0m')
            buy_price = f'${buy_price:.2f}USD'.rjust(12)
            price_change = f'-${-1*price_change:.2f}USD'.rjust(12) if price_change < 0 else f'${price_change:.2f}USD'.rjust(12)
            percent_change = f'{percent_change:.2f}%'.rjust(8)
        else:
            buy_price = 'idk'.rjust(12)
            price_change = 'idk'.rjust(12)
            percent_change = 'idk'.rjust(8)
        check_price = f'${check_price:.2f}USD'.rjust(12)
        return f'{buy_price} | {buy_date} | {check_price} | {check_date} | {change_color}{price_change} | {percent_change}{reset}'


if __name__ == "__main__":
    tracker = SteamPriceTracker(mode='load')
    tracker.display_collection()
