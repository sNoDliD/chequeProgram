# ParseCheque

## Installation

1. Install tesseract
```bash
sudo apt update sudo apt install tesseract-ocr
```
2. Install languages
```bash
wget https://github.com/tesseract-ocr/tessdata/raw/master/script/Hebrew.traineddata
sudo apt-get install tesseract-ocr-heb
sudo apt-get install tesseract-ocr-eng
```
and move it in tesseract-ocr folder
3. Install dependencies 
```bash
pip install -r req.txt
```
## Usage

```bash
python3 parse.py "data/5.jpg"
```

## License
[MIT](https://choosealicense.com/licenses/mit/)
