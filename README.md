# Do NOT use this bot to actually buy products from Gorilla Mind, this is purely for entertainment purposes only!

## How to use
1. You must be familiar with python and pip and have it set up on your machine.
2. Create an account on Gorilla Mind for fast checkout and enter a shipping address and set it as default with the checkbox. If you don't want to
   use an account to checkout and prefer to do it anonymously, you must leave ```email``` and ```password``` field as ```""``` in ```details.json```. You need to check if your destination country has a ```province``` attribute. For example the USA requires a state, and other countries may require you to provide one. In the case of if you choose to do a fast checkout with an account, provide this along with your login details and payment information.
   save this in your default shipping address on the site.
3. Enter your details in ```details.json```, there are some sample ones in there in begin with if you want to drive it for a test run.
   Set ```full_buy``` to ```false``` to test if your config works without actually completing the purchase.
3. run ```pip install -r requirements.txt``` to install all dependencies. 

## Running the bot
1. Run ```python app.py gorilla```.
2. Follow the prompts.
3. Have fun!

## Contributing
If you would like to contribute and fix issues, make a branch & pull request. Include a description of the fix and a GIF of the fix working in action.
Look at the issues tab in GitHub to see what needs fixing!

