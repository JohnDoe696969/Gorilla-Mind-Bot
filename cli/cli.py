import os
from os import path
import click
import json

from cli.utils import QuestionaryOption
from gorilla import Gorilla_Mind
from products import GORILLA_PRODUCTS
from utils import selenium_utils
from utils.logger import log

DETAILS_PATH = "details.json"

@click.group()
def main():
    pass


@click.command()
@click.option(
    "--item",
    type=click.Choice(GORILLA_PRODUCTS, case_sensitive=False),
    prompt="What product after you after?",
    cls=QuestionaryOption,
)
@click.option(
    "--quantity",
    type=int,
    prompt="How many do you want",
    default=lambda: int(os.environ.get("product_quantity", 1)),
    show_default="current user",
)
@click.option("--interval", type=int, default=2)




def gorilla(item, quantity, interval):
    config = False

    if path.exists(DETAILS_PATH):
        with open(DETAILS_PATH) as json_file:
            config = json.load(json_file)
    else:
        log.info('Your details config is incorrectly setup')   
    if(config):
        gorilla = Gorilla_Mind(item=item, quantity=quantity, interval=interval, config=config)

main.add_command(gorilla)
