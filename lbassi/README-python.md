# README-python — Spiegazione passo passo dello script

Questa guida spiega **riga per riga** cosa fa lo script
[`assignment.py`](assignment.py), partendo da zero. Non serve conoscere Python:
ogni concetto è spiegato con parole semplici.

> Idea di fondo: lo script si collega ai tre "dispositivi" di rete del laboratorio
> (RAN, Router, Core) e imposta gli indirizzi IP delle loro interfacce, usando il
> protocollo **NETCONF**. Invece di farlo a mano un comando alla volta, lo fa il
> programma per noi.

---

## 0. Concetti base di Python (30 secondi)

- **Variabile**: un nome a cui assegniamo un valore. Esempio: `porta = 830`.
- **Stringa**: del testo tra virgolette. Esempio: `"admin"`.
- **Lista** `[ ... ]`: un elenco ordinato di elementi.
- **Dizionario** `{ "chiave": valore }`: una specie di "scheda" con coppie
  etichetta → valore. Esempio: `{"nome": "RAN", "porta": 830}`.
- **Funzione** `def nome(...)`: un blocco di istruzioni con un nome, che possiamo
  richiamare quando vogliamo.
- **`for elemento in lista:`**: ripete le stesse istruzioni per ogni elemento.
- **`print(...)`**: scrive un messaggio a schermo.

Con questi 6 concetti capirai tutto lo script.

---

## 1. Import: portiamo dentro gli strumenti

```python
from ncclient import manager
from lxml import etree
```

- `ncclient` è la libreria che sa **parlare NETCONF** con i dispositivi.
  Da essa prendiamo `manager`, l'oggetto che apre le connessioni.
- `lxml` serve a **leggere e stampare l'XML** (il formato in cui i dispositivi
  rispondono). Da essa prendiamo `etree`.

Pensa a questi due `import` come "prendere gli attrezzi dalla cassetta prima di
iniziare a lavorare".

---

## 2. L'elenco dei dispositivi (`DEVICES`)

```python
DEVICES = [
    {
        "name": "RAN",
        "host": "127.0.0.1",
        "port": 830,
        "username": "admin",
        "password": "admin",
        "interfaces": [
            {"name": "eth0", "ip": "192.168.1.10", "prefix": "24"},
            {"name": "backhaul0", "ip": "10.0.1.1", "prefix": "30"},
        ],
    },
    ... (Router e Core)
]
```

`DEVICES` è una **lista di 3 dizionari**, uno per dispositivo. Ogni dizionario è
come una scheda che dice:

- `name`: nome leggibile (serve solo per i messaggi a schermo).
- `host`: l'indirizzo dove contattarlo (`127.0.0.1` = questo stesso computer).
- `port`: la porta (RAN=830, Router=831, Core=832).
- `username` / `password`: le credenziali (`admin`/`admin`).
- `interfaces`: la **lista delle interfacce** da configurare, ognuna con nome, IP
  e `prefix` (la lunghezza della maschera, es. `/24` o `/30`).

Questa è la parte che cambieresti se volessi usare indirizzi diversi: qui c'è
**tutta la configurazione**, separata dal codice. Il resto dello script è logica
che legge questi valori.

Gli indirizzi scelti rispettano la topologia del laboratorio:

| Dispositivo | eth0 | backhaul |
| ----------- | ---- | -------- |
| RAN    | `192.168.1.10/24` | `backhaul0` `10.0.1.1/30` |
| Router | `192.168.1.20/24` | `eth1` `10.0.1.2/30`, `eth2` `10.0.2.1/30` |
| Core   | `192.168.1.30/24` | `eth1` `10.0.2.2/30` |

---

## 3. I "modelli" di testo XML (i template)

I dispositivi NETCONF non capiscono l'italiano: vogliono ricevere ordini scritti
in **XML** (un formato con tag tra parentesi angolari, tipo `<nome>...</nome>`).

Per non riscrivere l'XML a mano ogni volta, prepariamo dei **modelli con dei
buchi** da riempire. I buchi sono le `{...}` (es. `{ip}`, `{prefix}`).

### 3a. Modello di una singola interfaccia

```python
INTERFACE_TEMPLATE = """
    <interface>
        <name>{name}</name>
        <ipv4 xmlns="..."
              xmlns:nc="..."
              nc:operation="replace">
            <enabled>true</enabled>
            <address>
                <ip>{ip}</ip>
                <prefix-length>{prefix}</prefix-length>
            </address>
        </ipv4>
    </interface>"""
```

- Le `"""..."""` (tre virgolette) permettono di scrivere testo su **più righe**.
- `{name}`, `{ip}`, `{prefix}` sono i "buchi" che riempiremo con i valori veri.
- `nc:operation="replace"` è importante: dice al dispositivo «**sostituisci**
  l'indirizzo esistente con questo». Grazie a questo lo script si può rilanciare
  quante volte vuoi senza errori (è "idempotente").

### 3b. Contenitore di tutte le interfacce

```python
CONFIG_TEMPLATE = """
<config ...>
    <interfaces ...>{interfaces}
    </interfaces>
</config>"""
```

È l'involucro esterno: dentro il buco `{interfaces}` incolleremo uno o più
blocchi `<interface>` generati con il modello precedente.

### 3c. Filtro per la lettura

```python
INTERFACES_FILTER = """
<filter ...>
    <interfaces .../>
</filter>"""
```

Quando **leggiamo** la configurazione, questo filtro dice al dispositivo «dammi
solo la parte delle interfacce, non tutto il resto».

---

## 4. Le funzioni (i "mattoncini" riutilizzabili)

Una funzione è un blocco di codice con un nome. La definiamo una volta e la
richiamiamo quando serve.

### 4a. `connect_device` — aprire la connessione

```python
def connect_device(device):
    conn = manager.connect(
        host=device["host"],
        port=device["port"],
        username=device["username"],
        password=device["password"],
        hostkey_verify=False,
        allow_agent=False,
        look_for_keys=False,
        timeout=10,
    )
    print(f"[{device['name']}] connected to {device['host']}:{device['port']}")
    return conn
```

- Riceve un `device` (una delle schede viste sopra).
- `manager.connect(...)` apre la sessione NETCONF con host, porta e credenziali
  presi dalla scheda. Le opzioni `hostkey_verify=False` ecc. servono solo a
  semplificare la connessione nel laboratorio (niente controlli di chiavi SSH).
- `print(...)` stampa un messaggio di conferma. La `f` davanti alle virgolette
  permette di inserire valori dentro il testo con le `{...}`.
- `return conn` restituisce la connessione aperta, così chi ha chiamato la
  funzione può usarla.

### 4b. `build_config` — costruire l'XML da inviare

```python
def build_config(device):
    blocks = "".join(
        INTERFACE_TEMPLATE.format(name=i["name"], ip=i["ip"], prefix=i["prefix"])
        for i in device["interfaces"]
    )
    return CONFIG_TEMPLATE.format(interfaces=blocks)
```

- Per **ogni interfaccia** `i` del dispositivo, prende il `INTERFACE_TEMPLATE` e
  con `.format(...)` riempie i buchi `{name}`, `{ip}`, `{prefix}`.
- `"".join(...)` incolla insieme tutti i blocchi ottenuti in un unico testo.
- Infine mette quel testo dentro `CONFIG_TEMPLATE` (nel buco `{interfaces}`) e lo
  restituisce. Risultato: l'XML completo e pronto da spedire.

### 4c. `edit_candidate` — scrivere nella "brutta copia"

```python
def edit_candidate(conn, device):
    config_xml = build_config(device)
    conn.edit_config(target="candidate", config=config_xml)
    names = ", ".join(i["name"] for i in device["interfaces"])
    print(f"[{device['name']}] edit-config -> candidate OK ({names})")
```

- Costruisce l'XML con `build_config`.
- `conn.edit_config(target="candidate", ...)` invia la configurazione al
  datastore **candidate**.

> **Cos'è il "candidate"?** Ogni dispositivo tiene 3 copie della configurazione:
> - **running**: quella attiva in questo momento;
> - **candidate**: una "brutta copia" dove provare le modifiche senza rischi;
> - **startup**: quella caricata al riavvio.
>
> Scrivere nel candidate **non cambia** subito il comportamento del dispositivo:
> è come modificare una bozza. Diventa reale solo dopo il `commit` (vedi sotto).

### 4d. `get_config` — leggere e mostrare la configurazione

```python
def get_config(conn, device, source):
    reply = conn.get_config(source=source, filter=INTERFACES_FILTER)
    xml = etree.tostring(reply.data_ele, pretty_print=True).decode()
    print(f"[{device['name']}] get-config <{source}>:\n{xml}")
```

- `conn.get_config(source=source, ...)` chiede la configurazione dal datastore
  indicato (`source` sarà `"candidate"` oppure `"running"`).
- `etree.tostring(..., pretty_print=True)` trasforma la risposta XML in testo
  ordinato e leggibile.
- `print(...)` lo mostra a schermo, così puoi controllare a occhio che sia giusto.

### 4e. `commit` — rendere reali le modifiche

```python
def commit(conn, device):
    conn.commit()
    print(f"[{device['name']}] commit OK (candidate -> running)")
```

- `conn.commit()` copia il contenuto del **candidate** dentro il **running**:
  da questo momento le modifiche sono **attive** sul dispositivo.

---

## 5. Il programma principale (`main`)

```python
def main():
    for device in DEVICES:
        conn = connect_device(device)
        try:
            edit_candidate(conn, device)                 # passo 2 + 3
            get_config(conn, device, source="candidate") # passo 4 (verifica)
            commit(conn, device)                         # passo 5
            get_config(conn, device, source="running")   # riconferma
        finally:
            conn.close_session()
        print("-" * 72)
```

Qui si mette tutto insieme. Per **ogni** dispositivo nella lista `DEVICES`:

1. `connect_device` → apre la connessione.
2. `edit_candidate` → scrive eth0 + backhaul nel candidate.
3. `get_config(... "candidate")` → mostra la bozza per controllarla.
4. `commit` → applica le modifiche (candidate → running).
5. `get_config(... "running")` → rilegge il running per confermare.

Dettagli utili:

- **`try: ... finally: ...`**: qualunque cosa succeda (anche un errore), il blocco
  `finally` viene sempre eseguito. Serve a chiudere sempre la connessione con
  `conn.close_session()` e non lasciarla aperta.
- `print("-" * 72)` stampa una riga di 72 trattini come separatore tra un
  dispositivo e l'altro.

### L'ultima riga

```python
if __name__ == "__main__":
    main()
```

È una formula standard di Python che significa: «se questo file viene lanciato
direttamente (e non importato da un altro), allora esegui `main()`». In pratica è
il **pulsante di avvio** dello script.

---

## 6. Come si esegue

Dal terminale, nella cartella del progetto:

```bash
python3 lbassi/assignment.py
```

Vedrai scorrere, per ogni dispositivo: la connessione, la conferma della scrittura
nel candidate, la configurazione letta, il commit e infine la configurazione
attiva nel running.

Per verificare che tutto sia coerente tra i tre dispositivi:

```bash
python3 network_check.py
```

Se è tutto a posto, ogni riga dei link mostra `✅ OK`.

---

## 7. Riepilogo in una frase

Lo script **legge la configurazione desiderata** dalla lista `DEVICES`, la
**trasforma in XML** con dei modelli, la **scrive nella bozza (candidate)** di
ogni dispositivo, la **controlla**, e infine la **conferma (commit)** rendendola
attiva. Tutto in automatico, per tutti e tre i dispositivi.
