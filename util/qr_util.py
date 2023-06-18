import logging
import os.path
import pathlib
import subprocess
import traceback

import zxing

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def get_qr_code(path: str):
    if not os.path.exists(path):
        logging.info("解析二维码，路径不存在")
        return None

    cmd = [
        'java',
        '-cp',
        '/usr/local/lib/python3.11/site-packages/zxing/java/*',
        'com.google.zxing.client.j2se.CommandLineRunner',
        pathlib.Path(path).absolute().as_uri()
    ]
    try:
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=False)
        except OSError as e:
            logging.info("track = %s", traceback.format_exc())
        else:
            stdout, stderr = p.communicate()
            logging.info(stdout)
            logging.info(stderr)
    except BaseException as e:
        logging.info("track = %s", traceback.format_exc())
    reader = zxing.BarCodeReader()
    try:
        logging.info("解析二维码，path = %s", path)
        barcode = reader.decode(path)
        if barcode:
            res = barcode.parsed
            logging.info("解析二维码, parsed = %s", res)
            return res
        else:
            logging.info("未找到二维码")
            return None
    except Exception as e:
        logging.info("解析二维码失败，path = %s, %s", path, str(e))
        logging.info("trace = %s", traceback.format_exc())
        return None


if __name__ == "__main__":
    # reader = zxing.BarCodeReader()
    # barcode = reader.decode("C:\\Users\\Zipper\\Pictures\\Screenshot_2023-06-16-20-00-50-853_com.tencent.mm.jpg")
    # if barcode:
    #     print(barcode.parsed)
    # else:
    #     print("未找到二维码")
    pass
