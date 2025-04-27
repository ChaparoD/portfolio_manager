from django.core.management.base import BaseCommand, CommandError
from assets import models
from ...utils.helpers import extract_instances, load_raw_prices, transform_prices


#Bulk insertion
class Command(BaseCommand):
    help = 'run etl for loading datos.xls file into database model'
    
    # def add_arguments(self, parser):
    #     parser.add_argument('arg_name', nargs='?', type=str, help='Description of argument')
    #     parser.add_argument('--option', action='store_true', help='Description of option')

    def handle(self, *args, **options):
        self.populate_asset_weights()
        
    #     # Command logic here
    #     arg_value = options['arg_name']
    #     option_value = options['option']

    #     self.stdout.write(self.style.SUCCESS(f'Successfully ran my command with arg: {arg_value} and option: {option_value}'))

    def populate_asset_weights(self):
        extract_instances()
        load_raw_prices()
        transform_prices()
       
