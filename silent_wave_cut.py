# -*- coding: utf-8 -*-

import os
import subprocess

import soundfile as sf
import numpy as np
# from matplotlib import pyplot as plt

import shutil  #folder operation
from tkinter import *  #version 8.6
from tkinter import ttk
import getpass
import tkinter.messagebox
from tkinter import filedialog

# from matplotlib.figure import Figure
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# add path to ffmpeg above to call it just as 'ffmpeg'

os.environ["PATH"] += os.pathsep + os.getcwd()
os.environ['PATH']

#####  fileChooser ###############
if not os.path.isdir("auto_slide_image"):  #フォルダがなかったら
    #####謎のウインドウを非表示にする回避策
    root = Tk()
    root.withdraw()
    user = getpass.getuser()
    iDir = 'C:/User/' + user + '/Desktop'
    tkinter.messagebox.showinfo('保存フォルダー',
                                '動画を保存するフォルダを選ぶ\n\n　　　または\n\nフォルダを作成してください')
    iDirPath = filedialog.askdirectory(initialdir=iDir)
    tkinter.messagebox.showinfo('動画ファイル',
                                'カットする動画を選んでください\n\n※ファイル名が日本語の場合エラーになります')
    #ファイル
    fTyp = [("", "*")]
    iFile = os.path.abspath(os.path.dirname(__file__))
    iFilePath = filedialog.askopenfilename(filetype=fTyp, initialdir=iFile)
    
    tkinter.messagebox.showinfo('カットの調整',
                                'カット音量(閾値)と\nカット前後の余白(ぶつ切りを防ぐ)\n\nを入力して下さい')
    root.destroy()




iFile_path = iFilePath.replace(
    '\\', '/'
)  #iFilePath.replace("\", "\\")  
iDir_path = iDirPath.replace(
    '\\', '/'
) #current_dir
iDir_name = "out"  #中間素材書き出しフォルダ名
outDir_path = "{}/{}".format(iDir_path, iDir_name)
out_sound_file = "{}/{}".format(outDir_path, "input.wav")
out_move_name = "out"
rate = 44100  #-ar(bps)
channel = 1  #音声のチャンネル数 2だと左右のスピーカー
padding_time = 0.3  #どれくらい動画前後の間を設けるか(デフォルト値)
th = 0.1  #音量閾値(デフォルト値)
min_silence_duration = 0.5  #何秒以上音がないところが続いたら音がないところと判断するか
fomat_eachmov = "mov"  #分割動画出力フォーマット
fomat_outmov = "mp4"  #最終出力動画フォーマット


#閾値調整
def th_padding_set():
    th = ""
    padding = ""
    # テキストボックスの作成 #
    root = Tk()
    root.minsize(width=300, height=150)
    root.title('音の閾値とその余白を設定してください')

    # ウィジェットの作成
    frame = ttk.Frame(root,padding=50)
    frame.grid()

    th = StringVar()#StringVarがないと文字が取得できない
    padding = StringVar()#
    th.set("0.05")
    label_th = ttk.Label(frame, text='音の閾値(dB)')
    label_th.grid(row=0, column=0)
    
    entry_th = ttk.Entry(frame, width=15,textvariable=th)
    entry_th.grid(row=0, column=1)

    padding.set("0.3")
    label_padding = ttk.Label(frame, text='前後の余白(sec)')
    label_padding.grid(row=1, column=0)
    entry_padding = ttk.Entry(frame,width=15,textvariable=padding)
    entry_padding.grid(row=1, column=1)

    
    button = ttk.Button(
        frame,
        text='OK',
        command = root.destroy
    ) 
    button.grid(row=2, column=0,columnspan=2)
    # ウィンドウの表示開始
    root.mainloop()
    
    #th,padding取得
    th = th.get()
    padding = padding.get()

    root = tkinter.Tk()
    root.withdraw()# 謎のウインドウを非表示にする回避策
    tkinter.messagebox.showinfo('実行','バックグラウンドで動作を開始します\n\n処理に時間がかかります')
    root.destroy()

    return float(th), float(padding)

def clean_dir(outDir_path):  #中間素材書き出しフォルダの中身を全削除
    if os.path.isdir(outDir_path):  #存在していたら
        shutil.rmtree(outDir_path)  #消す
    os.mkdir(outDir_path)  #新規作成


def load_data(iFile_path):  # return data, t, samplerate
    ## clean folder
    clean_dir(outDir_path)

    #move to path
    file_at_this_dir = os.path.dirname(iFile_path)
    os.chdir(file_at_this_dir)  #移動
    #take out fileName
    file_name = os.path.basename(iFile_path)  #ファイル名のみ取り出し(拡張子あり)

    ## mp4 out of wav
    cmd = "ffmpeg -y -i {} -ar {} -ac {} {}".format(file_name, rate, channel,
                                                    out_sound_file)
    subprocess.run(cmd, shell=True).returncode

    # load wav data
    data, samplerate = sf.read(out_sound_file)
    t = np.arange(
        0, len(data)) / samplerate  #1配列に入れる標本を決定 # print(len(t)) #939008配列存在する

    return data, t, samplerate


def show_data(th, padding_time):
    print("th=",th, "padding",padding_time)

    amp = np.abs(data)
    b = amp > th  #ある一定のthより大きい振幅かどうかが[True,Flase]でbへ格納されていく

    # pick up silence part
    silences = []
    prev = 0
    entered = 0
    for i, v in enumerate(b):
        if prev == 1 and v == 0:  # enter silence (ひとつ前は音があり、次で音が無くなった。)
            entered = i
        if prev == 0 and v == 1:  # exit silence (ひとつ前は音がなく、次で音がった。)
            duration = (i - entered) / samplerate
            if duration > min_silence_duration:
                silences.append({"from": entered, "to": i, "suffix": "cut"})
                entered = 0
        prev = v

    if entered > 0 and entered < len(b):
        silences.append({"from": entered, "to": len(b), "suffix": "cut"})

    #len(silences)=7, len(t)=939008, len(b)=939008

    # missed less 0.3
    cut_blocks = []  #最終的にカットしたい部分が記録される
    blocks = silences  #無音部分のリスト：[{"from": 始点, "to": 終点}, {"from": ...}, ...]

    cut_blocks = [
        blocks[0]
    ]  #最初のデータを入れる {'from': 307381, 'to': 343723, 'suffix': 'cut'}
    for i, b in enumerate(blocks):
        if i == 0:  #0回目は以下の処理を飛ばす
            continue
        interval = (b["from"] -
                    cut_blocks[-1]["to"]) / samplerate  #[-1]で配列の最後の要素を参照
        # カット対象だった場合
        if interval < padding_time:
            cut_blocks[-1]["to"] = b["to"]  #１つ前のtoを書き換え
        else:
            cut_blocks.append(b)  #カット対象ではなかったらそのまま追加

    ####### 波形表示 ############
    # _tmp = np.zeros(len(t))
    # for i in range(len(cut_blocks)):
    #     _tmp[cut_blocks[i]["from"]:cut_blocks[i]["to"]] = 1

    # # middleInfo()
    # #show wav
    # # plt.figure(figsize=(18, 6))
    # # plt.title('The parts of which green border-line enclosed will be cut')
    # # plt.plot(t, _tmp, color='forestgreen')
    # # plt.plot(t, data, color='silver')
    # # plt.show()
    # fig = Figure(figsize=(18, 6))
    # ax = fig.add_subplot(1, 1, 1)
    # ax.plot(t, _tmp, color='forestgreen')
    # ax.plot(t, data, color='silver')
    # ax.set_title('The parts of which green border-line enclosed will be cut')

    # root = Tk()
    # root.withdraw()
    # root.title(u"無音と判断した部分が緑の枠で囲われます。")
    # tkinter.messagebox.showinfo('info',
    #                             '次に波形が表示されます。\n\n音声波形のウインドウを閉じたら処理を開始します。')
    # # Canvas
    # canvas = FigureCanvasTkAgg(
    #     fig, master=root)  # Generate canvas instance, Embedding fig in root
    # canvas.draw()
    # canvas.get_tk_widget().pack()

    # root.update()
    # root.deiconify()
    # root.mainloop()

    return cut_blocks


def export_mov(cut_blocks):
    print(cut_blocks)
    # list up keeping part
    keep_blocks = []  #残す部分が記録される
    for i, block in enumerate(cut_blocks):
        if i == 0 and block["from"] > 0:  #配列の一番最初のみ
            keep_blocks.append({
                "from": 0,
                "to": block["from"],
                "suffix": "keep"
            })  #cut_blockの to と fromを反転させてkeep_blockに入れている
        if i > 0:
            prev = cut_blocks[i - 1]  #配列[1]以降
            keep_blocks.append({
                "from": prev["to"],
                "to": block["from"],
                "suffix": "keep"
            })  #前のblockのtoと次のblockのfromをつなげる
        if i == len(cut_blocks) - 1 and block["to"] < len(data):  #配列の一番最後
            keep_blocks.append({
                "from": block["to"],
                "to": len(data),
                "suffix": "keep"
            })

    # cut movie
    movs_path = "movs_path.txt"  #ffmpegを実行するところと同じ階層でないとだめみたい
    # movs_path = "{}/movs_path.txt".format(outDir_path)
    movs_list = []

    for i, block in enumerate(keep_blocks):
        fr = max(block["from"] / samplerate - padding_time, 0)  #fr=from
        to = min(block["to"] / samplerate + padding_time,
                 len(data) / samplerate)
        duration = to - fr
        out_path = "{}/{}.{}".format(outDir_path, i, fomat_eachmov)  #filename
        # 出力用テキストファイルにpathを追加
        movs_list.append("file " +
                         out_path.replace("\\", "/"))  #file sample.mp4の形式でかく
        # ブロックごとに動画出力
        output_cmd = "ffmpeg -y -ss {} -i {} -t {} {}".format(
            fr, str(iFile_path), duration, str(out_path))
        subprocess.run(output_cmd, shell=True).returncode
    #テキストファイルにファイル名(コマンド)を書き込み
    with open(movs_path, mode='w', encoding="utf-8") as fw:
        fw.write('\n'.join(movs_list))

    #動画結合
    outmove_path = "{}\{}.{}".format(outDir_path, out_move_name,
                                     fomat_outmov)  #filename
    # outmove_path = "{}/{}.{}".format(outDir_path ,out_move_name, fomat_outmov)  #filename
    print("###############", outmove_path)
    print(movs_path)
    combinemovie_cmd = "ffmpeg -y -f concat -safe 0 -i {} -c copy {}".format(
        movs_path, outmove_path)
    subprocess.run(combinemovie_cmd, shell=True).returncode


def endInfo(outDir_path):
    root = Tk()
    root.withdraw()
    tkinter.messagebox.showinfo(
        'info', '処理が終了しました\n\n出力動画はout.mp4です\n出力先：' + outDir_path)
    root.destroy()


# def middleInfo():

# #ラベルの値変更
# def change_valdb(*args, val_db, text_db):
#     _value = round(val_db.get() / 1000,2)
#     text_db.set("{}".format(_value, '.2f'))

# def change_valpadding(*args, val_padding, text_padding):
#     _value = round(val_padding.get() / 100, 2)
#     text_padding.set("{}".format(_value, '.2f'))

# def setVal():
#     ##  setVal ########################################################
#     root = Tk()
#     root.title('Wav Cube')

#     #表示用のテキスト作成
#     text_db = StringVar()
#     text_db.set("0")
#     text_padding = StringVar()
#     text_padding.set("0")
#     label_padding = Label(textvariable=text_padding,
#                         bg="tan",
#                         font=("Arial", 14, "bold"))
#     label_db = Label(textvariable=text_db, bg="tan", font=("Arial", 14, "bold"))
#     val_db = DoubleVar()  #doubleで値を取得
#     val_db.set(0.05)
#     val_db.trace("w", change_valdb(val_db, text_db))  #関数とスケールの動きをリンク

#     exp_db = Label(text='カット音量最大値　(初期値:0.05)', font=("メイリオ", 10))
#     exp_padding = Label(text='カット前後の余白　(初期値:0.3)', font=("メイリオ", 10))

#     val_padding = DoubleVar()  #doubleで値を取得
#     val_padding.set(0.3)
#     val_padding.trace("w", change_valpadding(val_padding, text_padding))  #関数とスケールの動きをリンク
#     sc_padding = ttk.Scale(root, from_=0, to=100, length=200, variable=val_padding)
#     sc_db = ttk.Scale(root, from_=0, to=150, length=200, variable=val_db)

#     #要素
#     button_export = ttk.Button(root, text='出力', command=export_mov)
#     button_reshow = ttk.Button(root, text='再計算', command=show_data(val_db,val_padding))

#     #配置
#     # video.grid(row=0, column=0, sticky=(N, E, S, W)) #sticky=(N, E, S, W)で中央寄せ
#     sc_db.grid(row=1, column=1)
#     sc_padding.grid(row=3, column=1)

#     exp_db.grid(row=0, column=1, pady=10)
#     exp_padding.grid(row=2, column=1, pady=10)

#     label_db.grid(row=1, column=2)
#     label_padding.grid(row=3, column=2)

#     button_reshow.grid(row=4, column=0, padx=20, pady=20)
#     button_export.grid(row=4, column=2, padx=20, pady=20)

#     root.mainloop()

### Main ##########################################################
try:
    clean_dir(outDir_path)  #フォルダ削除
    th, padding_time = th_padding_set()
    data, t, samplerate = load_data(iFile_path)  #動画読み込み
    cut_blocks = show_data(th, padding_time)  #波形表示
    export_mov(cut_blocks)
    endInfo(outDir_path)
except Exception as e:
    root = Tk()
    root.withdraw()
    etype = str(type(e))
    eargs = str(e.args)
    e =  str(e)
    tkinter.messagebox.showinfo('エラー', 'errorType:' +'\n' + etype + '\n\n' +'errorArgs:'+ '\n' + eargs  + '\n\n' +'errorMessage:'+'\n'+ e)
    root.destroy()