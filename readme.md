# 如何打包
```bash
cd 你的项目文件夹

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

pip install tcod pillow

pip install pyinstaller

pyinstaller --onefile --noconsole main.py --add-data "assets;assets"

```