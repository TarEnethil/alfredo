function teig() {
    if [ $# -ne 1 ]; then
        echo "usage: teig <anzahl teilnehmer>"
        return
    fi

    echo "Teig für $1 Personen ($((200*$1)) Gramm):"
    echo "Mehl $((125*$1))g"
    echo "Wasser $((75*$1))ml"
}
