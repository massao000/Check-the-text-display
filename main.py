import TkEasyGUI as eg
from PIL import Image, ImageDraw, ImageFont
import io
import winreg
import os

def get_windows_font_paths():
    """Windowsのレジストリからフォントのファイルパス一覧を取得します。"""
    font_paths = {}
    
    # 登録されているフォント情報があるレジストリキー
    reg_path = r"Software\Microsoft\Windows NT\CurrentVersion\Fonts"
    
    try:
        # レジストリキーを開く
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
        
        i = 0
        while True:
            try:
                # 値を順番に取得
                name, value, type = winreg.EnumValue(key, i)
                
                # ファイルパスの値を取得 (通常はstr)
                font_filename = value
                
                # フォントファイルのフルパスを構築 (通常はC:\Windows\Fontsにある)
                # 環境によってはパスが異なる場合があるので注意
                if "\\" not in font_filename and "/" not in font_filename:
                    # ファイル名のみの場合、標準のフォントディレクトリを付加
                    font_dir = os.path.join(os.environ['WINDIR'], 'Fonts')
                    full_path = os.path.join(font_dir, font_filename)
                else:
                    # フルパスや相対パスが記録されている場合
                    full_path = font_filename

                font_paths[name] = full_path
                i += 1
            except OSError:
                # 全ての値を読み終えるとOSErrorが発生する
                break
        
        winreg.CloseKey(key)
    except Exception as e:
        print(f"レジストリの読み取り中にエラーが発生しました: {e}")

    return font_paths


def calc_alignment(block_w, block_h, img_w, img_h, align, position_y, is_position_y):
    """テキストブロック全体の位置を画像内で揃える"""
    
    if is_position_y:
        positions = {
            "自由入力": [None, None],
            "左上": [(0, position_y), None],
            "上中央": [((img_w - block_w) // 2, position_y), None],
            "右上": [(img_w - block_w, position_y), None],
            "左中央": [(0, position_y), None],
            "中央": [((img_w - block_w) // 2, position_y), "mm"],
            "右中央": [(img_w - block_w, position_y), None],
            "左下": [(0, img_h - position_y), None],
            "下中央": [((img_w - block_w) // 2, position_y), None],
            "右下": [(img_w - block_w, position_y), None],
        }
    else:
        positions = {
            "自由入力": [None, None],
            "左上": [(0, 0), None],
            "上中央": [((img_w - block_w) // 2, 0), None],
            "右上": [(img_w - block_w, 0), None],
            "左中央": [(0, (img_h - block_h) // 2), None],
            "中央": [((img_w - block_w) // 2, (img_h - block_h) // 2), "mm"],
            "右中央": [(img_w - block_w, (img_h - block_h) // 2), None],
            "左下": [(0, img_h - block_h), None],
            "下中央": [((img_w - block_w) // 2, img_h - block_h), None],
            "右下": [(img_w - block_w, img_h - block_h), None],
        }
    return positions.get(align, None)

def draw_textA(values):
    global font_files
    # 画像サイズ
    img_w = int(values["-W-"])
    img_h = int(values["-H-"])
    
    # テキスト
    text = values["-TEXT-"]
    font_path = font_files.get(values["-FONT-"], "") if values["-FONT-"] else None
    font_size = int(values["-FONT_SIZE-"])
    
    text_color = values["-TEXT_COLOR-"]
    align = values["-ALIGN-"]
    
    anchor = values["-ANCHOR-"]
    
    # テキストのアウトライン
    stroke_color = values["-STROKE_COLOR-"]
    stroke_width = int(values["-STROKE-"])
    
    # テキスト座標
    x = int(values["-X-"])
    y = int(values["-Y-"])

    # 画像作成
    img = Image.new("RGB", (img_w, img_h), "#C5C5C5")
    draw = ImageDraw.Draw(img)

    # フォント
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()

    if align == "左":
        align = "left"
    elif align == "中央":
        align = "center" 
    else:  # 右
        align = "right" 


    # 行ごとのサイズ計測
    lines = text.split("\n")
    line_height = font.getbbox("A")[3]
    line_widths = [
        draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)[2]
        for line in lines
    ]

    block_w = max(line_widths)
    block_h = line_height * len(lines)
    
    # 自動位置決め
    pos = calc_alignment(block_w, block_h, img_w, img_h, anchor, y, values['-Y_POSITION-'])
    if pos[0] is not None:
        x, y = pos[0]
    
    if pos[1] is not None:
        anchor = pos[1]
    
    # テキスト描画
    draw.text(
        (x, y),
        text,
        fill=text_color,
        font=font,
        align=align,
        # anchor=anchor,
        stroke_width=stroke_width,
        stroke_fill=stroke_color,
    )
    
    window['-NOW_POSITION-'].update(text=f"x：{x} \ny：{y}")

    return img    



font_files = get_windows_font_paths()

font_names = [font_name for font_name, path in list(font_files.items())]

s = list(range(10, 255))

layout_setting = [
    [eg.Text("テキスト（複数行OK）")],
    [eg.Multiline("Hello\nWorld", key="-TEXT-", size=(30, 5))],
    [
        eg.Frame(
            "フォント", 
            layout=[
                [eg.Combo(font_names, default_value=font_names[0], key="-FONT-", expand_x=True)],
                [eg.Push(), eg.Combo(s, default_value='50', key="-FONT_SIZE-")]
                ], expand_x=True
            )
    ],
    [
        eg.Frame(
            "テキスト色 (16進数)", 
            layout=[[
                eg.Input("#000000", key="-TEXT_COLOR-", expand_x=True),
                eg.ColorBrowse("カラー選択")
                ]], expand_x=True
            )
    ],
    [
        eg.Frame(
            "座標", 
            layout=[
                [eg.Push(), eg.Combo(
                    [
                        "自由入力", "左上", "上中央", "右上",
                        "左中央", "中央", "右中央",
                        "左下", "下中央", "右下"
                    ], 
                    # default_value='mm', 
                    default_value='自由入力', 
                    key='-ANCHOR-')
                ],
                [eg.Label("x: "), eg.Input("50", key="-X-", expand_x=True)],
                [eg.Label("y: "), eg.Input("50", key="-Y-", expand_x=True)],
                [eg.Push(), eg.Checkbox("高さ調整", default=False, key='-Y_POSITION-')]
            ], expand_x=True
            )
    ],
    [
        eg.Frame(
            "アウトライン色", 
            layout=[[
                eg.Input("#FFFFFF", key="-STROKE_COLOR-", expand_x=True),
                eg.ColorBrowse("カラー選択")
                ]], expand_x=True
            )
    ],
    [
        eg.Frame(
            "線幅（アウトライン）", 
            layout=[
            [eg.Input("2", key="-STROKE-", expand_x=True)],
            ], expand_x=True
            )
    ],
    [
        eg.Frame(
            "テキストの詰め", 
            layout=[
                [eg.Push(), eg.Combo(['左', '中央', '右'], default_value='左', key='-ALIGN-')],
            ], expand_x=True
            )
    ],
    [
        eg.Frame(
            "画像サイズ", 
            layout=[
            [eg.Label("w: "), eg.Input("600", key="-W-", expand_x=True)],
            [eg.Label("h: "), eg.Input("300", key="-H-", expand_x=True)],
            ], expand_x=True
            )
    ],
    [eg.Button("更新"), eg.Button("終了")],
]

layout_preview = [
    [eg.Text("プレビュー（半分のサイズで表示）")],
    [eg.Image(key="-IMAGE-", expand_x=True, expand_y=True)],
    [
        eg.Frame(
            "現在のポジション", 
            layout=[
            [eg.Text("", key='-NOW_POSITION-')],
            ], expand_x=True
            )
    ],
]

layout_setting_c = eg.Column(layout_setting)
layout_preview_c = eg.Column(layout_preview)

layout = [
    [layout_setting_c, eg.VSeparator(), layout_preview_c],
]

window = eg.Window("複数行テキスト対応 Pillow テキスト描画 GUI", layout, finalize=True)


# 初期描画
bio = io.BytesIO()
Image.new("RGB", (600 // 2, 300 // 2), (255, 255, 255)).save(bio, format="PNG")
window["-IMAGE-"].update(data=bio.getvalue())


# メインループ
while True:
    event, values = window.read()
    if event in (eg.WIN_CLOSED, "終了"):
        break

    if event == "更新":
        img = draw_textA(values)
        
        resized_img = img.resize((img.width // 2, img.height // 2))

        bio = io.BytesIO()
        resized_img.save(bio, format="PNG")
        window["-IMAGE-"].update(data=bio.getvalue(), size=(resized_img.width, resized_img.height))

window.close()
