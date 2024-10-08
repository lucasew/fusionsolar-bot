#!/usr/bin/env -S sd nix shell --really
#!nix-shell -i python3 -p python3Packages.selenium chromedriver chromium

import subprocess
import tempfile
from urllib.request import urlopen, Request
import json
from argparse import ArgumentParser
from pathlib import Path
import time
import base64
import os
from sys import stderr
import email, smtplib, ssl
from shutil import which
from datetime import datetime

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

parser = ArgumentParser()
parser.add_argument("--user", default=os.getenv("FUSIONSOLAR_USER"), type=str)
parser.add_argument("--password", default=os.getenv("FUSIONSOLAR_PASSWORD"), type=str)
parser.add_argument('--smtp-user', default=os.getenv("SMTP_USER"))
parser.add_argument('--smtp-passwd', default=os.getenv("SMTP_PASSWD"))
parser.add_argument('--smtp-server', default=os.getenv("SMTP_SERVER"))
parser.add_argument('--smtp-destinations', default=os.getenv("SMTP_DESTINATIONS"))
parser.add_argument('--headless', action='store_true')
parser.add_argument('--verbose', '-v', action='store_true')
args = parser.parse_args()

enable_email = None not in [args.smtp_user, args.smtp_passwd, args.smtp_server, args.smtp_destinations]
if not enable_email:
    print("[!] Funcionalidade de email desativada", file=stderr)

now = datetime.today()

message = None
if enable_email:
    message = MIMEMultipart()
    message['From'] = args.smtp_user
    message['To'] = args.smtp_destinations.replace(' ', ', ')
    message["Subject"] = f"Relatório do dia {str(now).split(' ')[0]} FusionSolar"

if None in [args.user, args.password]:
    print("[!] Usuário e senha fusionsolar não fornecido")
    exit(1)

with tempfile.TemporaryDirectory() as tmpdir:
    service_args = []
    if args.verbose:
        service_args.append('--verbose')
    service = webdriver.chrome.service.Service(
        executable_path=which("chromedriver"),
        service_args=service_args,
        log_output=subprocess.STDOUT
    )
    chrome_options = webdriver.ChromeOptions()
    if args.headless:
        chrome_options.headless = True
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
    if args.verbose:
        chrome_options.add_argument('--log-level=DEBUG')
    chrome_options.add_argument(f'--user-data-dir={tmpdir}')
    chrome_options.add_argument('--window-size=1280,720')
    chrome_options.add_argument('--remote-debugging-pipe')
    driver = webdriver.Chrome(
        options=chrome_options,
        service=service
    )

    # driver.delete_all_cookies()
    # driver.execute_cdp_cmd('Storage.clearDataForOrigin', {
    #     "origin": '*',
    #     "storageTypes": 'all',
    # })

    while True:
        print('[*] Login', file=stderr)
        driver.get("https://intl.fusionsolar.huawei.com/pvmswebsite/login/build/index.html#/LOGIN")
        time.sleep(10)
        driver.find_element(By.CSS_SELECTOR, "div#username input").send_keys(args.user)
        password_input = driver.find_element(By.CSS_SELECTOR, "div#password input")
        password_input.send_keys(args.password)
        password_input.send_keys(Keys.ENTER)
        time.sleep(10)

        cooke_close_buttons = driver.find_elements(By.CSS_SELECTOR, "i.cookiePolicy-icon")
        for cooke_close_button in cooke_close_buttons:
            print('[*] Fechando diálogo de cookie ocupando espaço', file=stderr)
            cooke_close_button.click()

        shitty_modal_candidates = driver.find_elements(By.CSS_SELECTOR, "div.dpdesign-modal.nco-privacy-confirm-modal")
        if len(shitty_modal_candidates) > 0:
            print('[*] Encontrada porcaria de modal para autorização de espionagem', file=stderr)
            shitty_modal = shitty_modal_candidates[0]
            shitty_checkbox = shitty_modal.find_element(By.CSS_SELECTOR, "input")
            if shitty_checkbox.is_selected:
                shitty_checkbox.click()
            for shitty_button in shitty_modal.find_elements(By.CSS_SELECTOR, "button"):
                if shitty_button.text == 'Approve':
                    shitty_button.click()
                    break

            time.sleep(1)

            shitty_button.click()
            time.sleep(10)
        if 'login' not in driver.current_url:
            break
        else:
            print('[*] Reiniciado pra login, refazendo processo')

    stations_data = []
    remaining_trys = 5

    while len(stations_data) == 0:
        # if 'view/station' in driver.current_url:
        #     print('[*] Redirecionamento corno realizado, pulando etapa', file=stderr)
        #     print('[*] URL do redirecionamento corno: ', driver.current_url)
        #     stations_data.append(dict(
        #         url=driver.current_url,
        #         name="Unica",
        #     ))
        #     break
        print('[*] Homepage', file=stderr)
        driver.get("https://intl.fusionsolar.huawei.com")
        time.sleep(10)
        print('[*] Tentando listar estações', file=stderr)
        stations = driver.find_elements(By.CSS_SELECTOR, "a.nco-home-list-text-ellipsis")
        print('stations', stations, file=stderr)
        if len(stations) == 0:
            print("[*] Zero estações encontradas, tentando de novo", file=stderr)
            remaining_trys -= 1
            print("[*] URL atual: ", driver.current_url, file=stderr)
            if remaining_trys == 0:
                print('[*] Sem estações, desistindo...', file=stderr)
                exit(1)
        for station in stations:
            station_data = dict(
                url=station.get_attribute('href'),
                name=station.text 
            )
            print(station_data, file=stderr)
            stations_data.append(station_data)

    email_text = []

    email_text.append("Quantidade de energia produzida em cada base")
    email_text.append("")


    attachments = []
    for station in stations_data:
        station_url = station['url']
        station_name = station['name']
        print(f'[*] Chupinhando dados da estação "{station_name}"', file=stderr)
        driver.get(station_url)
        time.sleep(10)
        the_canvas = driver.find_element(By.CSS_SELECTOR, ".nco-single-energy-body canvas")
        canvas_b64 = driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", the_canvas)
        amount_produced = float(driver.find_element(By.CSS_SELECTOR, "span.value").text.replace(',', '.'))
        email_text.append(f"{station_name}: {amount_produced}kWh")
        print(f'[*] Produzido hoje: {amount_produced}kWh', file=stderr)
        print(f'[*] Salvando dados da estação "{station_name}"', file=stderr)

        image_to_embed = MIMEBase("image", "png")
        image_to_embed.set_payload(base64.b64decode(canvas_b64))
        encoders.encode_base64(image_to_embed)
        image_to_embed.add_header("Content-Disposition", f"attachment; filename= {station_name}.png")
        attachments.append(image_to_embed)

    email_text.append("")
    email_text.append("Os gráficos de geração estão em anexo.")
    email_text.append("")
    email_text.append(f"Dados obtidos em: {str(now)}")
    print(email_text)


    if enable_email:
        message.attach(MIMEText("\n".join(email_text), 'plain'))
        for attachment in attachments:
            message.attach(attachment)

        context = ssl.create_default_context()
        smtp_server, *smtp_port = args.smtp_server.split(":")
        if len(smtp_port) == 0:
            smtp_port = 465
        else:
            smtp_port = int(smtp_port[0])

        print('[*] Enviando emails', file=stderr)

        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(args.smtp_user, args.smtp_passwd)
            email_txt = message.as_string()
            server.sendmail(args.smtp_user, args.smtp_destinations.split(" "), email_txt)
    
    driver.quit()
