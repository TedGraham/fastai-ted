# fastai-ted

Built a batch image downloader that does a Bing image search and downloads the resulting images.  Heavily based on 
https://www.pyimagesearch.com/2018/04/09/how-to-quickly-build-a-deep-learning-image-dataset/, I recommend following
his directions get to get an API key.  Searches are free for 7 days and reasonably priced after that; I estimate building
a dataset of 50 categories, each with 100 images, would cost less that $1 USD.  

Examples:

Do a search for a single category, stored sequentially named images into the sportscars folder
>  python3 download_bing_images.py --output "datasets/sportscars" --query "1965 ford mustang" --apikey YOUR_KEY_HERE
 
Go through the sportscars.txt file, searching on each line individually
>  python3 download_bing_images.py --output "datasets/sportscars" --file sportscars.txt --apikey YOUR_KEY_HERE
