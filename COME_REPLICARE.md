# Come replicarlo da un cliente

Guida pratica per usare la riconciliazione su dati veri. Non serve saper programmare: si lavora con file Excel e due comandi.

> **Riservatezza.** Estratti conto e partite aperte restano sul tuo PC o su quello del cliente. La cartella `data/` è esclusa da GitHub: non caricare mai file del cliente nel repository.

## 1. Preparare il PC (una volta sola)

1. Installa **Python** da [python.org/downloads](https://www.python.org/downloads/). Su Windows spunta **"Add python.exe to PATH"** nella prima schermata. L'installazione per il solo utente non richiede diritti di amministratore.
2. Scarica il progetto: in alto su questa pagina, pulsante verde **Code → Download ZIP**, poi estrai la cartella.
3. Apri la cartella in Esplora file, scrivi `cmd` nella barra dell'indirizzo e premi Invio.
4. Installa le librerie (una volta sola):

   ```
   pip install -r requirements.txt
   ```

## 2. Prova con i dati di esempio

```
python generate_sample_data.py
python reconcile.py --no-ai
```

Apri il file in `output\`: devono risultare 24 movimenti abbinati su 27. Se funziona, il PC è pronto.

## 3. Dati da chiedere al cliente

Svuota la cartella `data\` e mettici due file (Excel o CSV, va bene anche il formato italiano con `;` e la virgola decimale):

| File | Cosa contiene | Da dove si prende |
|---|---|---|
| `bank_statement.xlsx` | Movimenti del conto nel periodo | Home banking → lista movimenti → esporta in Excel/CSV |
| `open_items.xlsx` | Fatture clienti e fornitori aperte | Business Central: **Movimenti clienti** e **Movimenti fornitori** con filtro *Aperto = Sì* → *Apri in Excel*, poi incolla le righe dei fornitori sotto quelle dei clienti, nelle stesse colonne |

Colonne che lo script cerca (riconosce i nomi in italiano e in inglese):

- **bank_statement**: Data contabile, Descrizione (o Causale), Importo. Se la banca esporta due colonne separate **Entrate** e **Uscite** (o Avere e Dare), lo script le unisce da solo.
- **open_items**: Nr. documento, Nome cliente (o Nome fornitore), Data scadenza, Importo residuo.

Se una colonna ha un nome diverso, lo script si ferma e scrive quale manca e quali ha trovato: basta rinominarla nel file.

**Segni.** Incassi positivi e pagamenti negativi sia in banca sia nelle partite: fatture clienti positive, fatture fornitori negative, come le esporta Business Central.

## 4. Lanciare la riconciliazione

```
python reconcile.py --no-ai
```

- `--fee-tolerance 20` è la differenza massima accettata come commissione trattenuta dalla banca (di default 20 €).
- Il risultato è in `output\`: foglio **Summary** con i numeri, **Bank lines** con l'esito riga per riga (verde abbinato, giallo proposta AI, rosso da verificare), **Open items** con le fatture ancora aperte.

### Con l'AI (facoltativo)

Per i movimenti che le regole non risolvono, l'AI propone un abbinamento con la motivazione.

1. Crea una chiave su [console.anthropic.com](https://console.anthropic.com) (pagamento a consumo: pochi centesimi per estratto conto).
2. Nel Prompt dei comandi: `set ANTHROPIC_API_KEY=la-tua-chiave`, poi `python reconcile.py`.

> Con l'AI i movimenti non abbinati e le partite aperte vengono inviati ad Anthropic. **Chiedi prima il consenso del cliente**, e se non c'è usa `--no-ai`.

## 5. Controlli prima di consegnare

1. **Abbinamenti "Nome + importo".** Controllane a campione qualcuno: sono corretti quasi sempre, ma un cliente con due fatture dello stesso importo può essere abbinato alla fattura sbagliata.
2. **Commissioni.** La colonna *Difference* mostra le commissioni trattenute: vanno registrate in contabilità.
3. **Proposte AI.** Non sono mai automatiche: ognuna va confermata o scartata a mano.
4. **Quadratura.** Saldo iniziale + movimenti = saldo finale dell'estratto conto.

## 6. Cosa consegnare

- Il file Excel con l'elenco di cosa registrare (incassi, pagamenti, commissioni) e cosa chiarire (movimenti rossi).
- In un progetto vero, il passo successivo è scrivere gli abbinamenti direttamente nel giornale di riconciliazione pagamenti di Business Central.
