import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
from openai import OpenAI
import av
import tempfile
import wave

client = OpenAI(api_key=st.secrets["openai_api_key"])

# Fragen definieren
fragen = [
    #Case 1
    "In deinem Team, das hauptsächlich im Homeoffice arbeitet, "
    "kommt es zu einem Missverständnis: Zwei Teammitglieder – "
    "Laura (Projektleitung) und Tim (Fachmitarbeiter) – haben sich über "
    "die Zuständigkeit für die Erstellung eines Projektberichts nicht "
    "eindeutig abgestimmt. Beide dachten, der jeweils andere sei "
    "verantwortlich. Am Tag der internen Abgabe ist kein Bericht "
    "vorhanden. Die Stimmung ist angespannt, Laura fühlt sich von Tim im "
    "Stich gelassen, Tim hingegen findet, dass die Aufgabenverteilung nie "
    "klar war. Im Team-Chat wurden zudem einige Nachrichten aus dem Z"
    "usammenhang gerissen interpretiert, was das Ganze zusätzlich emotional "
    "aufgeladen hat. Sie sind die Führungsperson des Teams. Wie gehen Sie als "
    "Führungsperson mit dieser Situation um? Nennen Sie mindestens drei "
    "konkrete Möglichkeiten, wie Sie auf dieses Missverständnis reagieren "
    "könnten – sowohl kurzfristig zur Klärung als auch langfristig zur "
    "Vorbeugung ähnlicher Situationen.",
    #Case 2
    "Du führst als Teamleitung ein Feedbackgespräch mit einem Mitarbeitenden, "
    "der in letzter Zeit wiederholt Deadlines verpasst hat. Der Mitarbeitende "
    "wirkt im Gespräch angespannt und sagt: „Ich habe einfach zu viele Aufgaben "
    "gleichzeitig. Ich weiß ehrlich gesagt gar nicht mehr, worauf ich noch "
    "achten soll. Statt auf deine Nachfragen einzugehen, wirkt er defensiv. "
    "Du spürst, dass sich hinter der Aussage mehr verbirgt, bekommst aber "
    "zunächst keine weiteren Informationen. Welche Rolle spielt aktives Zuhören für Sie in dieser Situation?"
    "Erklären Sie anhand des Falles, wie Sie durch aktives Zuhören zu einer "
    "besseren Gesprächsqualität und Lösungsfindung beitragen würden. Nennen "
    "Sie mir mindestens drei konkrete Verhaltensweisen oder Techniken, die Sie "
    "in diesem Gespräch anwenden würden.",
    #Case 3 
    "In deinem Projektteam häufen sich kleine Spannungen: Ein Kollege, den du fachlich sehr schätzt, "
    "unterbricht dich in Meetings regelmässig, wenn du deine Vorschläge präsentierst."
    "Beim letzten Mal hast du dich übergangen gefühlt, weil er sofort "
    "seine eigene Lösung eingebracht hat, bevor du deinen Gedanken zu Ende "
    "erklären konntest. Du möchtest das Thema ansprechen – ohne Vorwurf, aber klar "
    "und lösungsorientiert.Wie setzen Sie Ich-Botschaften in solchen Situationen im Berufsalltag ein?"
    "Erklären Sie anhand des Falls, wie eine Ich-Botschaft wirken kann."
    "Nennen Sie mindestens drei zentrale Elemente, die eine gelungene Ich-Botschaft ausmachen.",
    #Case 4 
    "Du bist Berufsbildner:in und führst ein Gespräch mit einer Auszubildenden im "
    "ersten Lehrjahr, die in letzter Zeit wiederholt zu spät gekommen ist. Du "
    "hast das Thema bereits einmal angesprochen. Nun sitzt sie dir im Gespräch "
    "gegenüber, mit verschränkten Armen, gesenktem Blick und antwortet nur knapp. Du möchtest das "
    "Gespräch nicht eskalieren lassen, sondern ein Klima schaffen, in dem sich "
    "die Auszubildende öffnen kann. Dabei willst du deine eigene nonverbale "
    "Kommunikation bewusst einsetzen. Was ist für Sie gute nonverbale Kommunikation im Berufsalltag? "
    "Beziehen Sie sich auf die Situation im Fallbeispiel und nennen Sie mindestens drei "
    "konkrete Elemente, mit denen Sie als Führungsperson oder "
    "Ausbildungsverantwortliche:r eine konstruktive Gesprächsatmosphäre fördern würden.",
    #Case 5
    "In einer Feedbackrunde mit deinem Team merkst du als Führungsperson, dass die Stimmung zunehmend "
    "gereizt wird. Ein Teammitglied formuliert sein Feedback sehr direkt („Ich finde, das war einfach "
    "schlecht vorbereitet.“), woraufhin eine Kollegin sichtbar die Augen verdreht und sich zurücklehnt. "
    "Andere schweigen oder wirken angespannt.nDu hast das Gefühl, dass die Art der "
    "Kommunikation gerade mehr belastet als nützt und möchtest die Situation nicht weiter eskalieren lassen."
    "Wie nutzen Sie Metakommunikation im Führungsalltag? Beziehen Sie sich "
    "auf das Fallbeispiel und erläutern Sie, wie Sie durch metakommunikative "
    "Elemente zu einem besseren Miteinander beitragen würden. Nennen Sie mindestens drei konkrete Möglichkeiten, "
    "wie Metakommunikation in dieser Situation helfen kann."
]
anzahl_fragen = len(fragen)

# Session-Variablen
if "frage_index" not in st.session_state:
    st.session_state.frage_index = 0
if "transkriptionen" not in st.session_state:
    st.session_state.transkriptionen = [""] * anzahl_fragen
if "audio_frames" not in st.session_state:
    st.session_state.audio_frames = []
if "bewertung_je_frage" not in st.session_state:
    st.session_state.bewertung_je_frage = []
if "bewertung_abgeschlossen" not in st.session_state:
    st.session_state.bewertung_abgeschlossen = False

# Audioaufnahme-Logik
class AudioProcessor(AudioProcessorBase):
    def __init__(self) -> None:
        self.frames = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray()
        self.frames.append(audio)
        return frame

    def get_frames(self):
        return self.frames

st.title("🎤 Mündliche Prüfungssequenz (HF Kommunikation)")

index = st.session_state.frage_index

if index < anzahl_fragen:
    st.subheader(f"Frage {index + 1} von {anzahl_fragen}")
    st.write(fragen[index])

    # Audioaufnahme
    ctx = webrtc_streamer(
        key=f"aufzeichnung_{index}",
        mode=WebRtcMode.SENDONLY,
        audio_processor_factory=AudioProcessor,
        media_stream_constraints={"audio": True, "video": False}
    )

    if ctx.audio_processor:
        if st.button("🎙️ Aufnahme speichern & transkribieren"):
            frames = ctx.audio_processor.get_frames()
            wav_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(48000)
                for f in frames:
                    wf.writeframes(f.tobytes())

            with open(wav_path, "rb") as file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=file
                )
            st.session_state.transkriptionen[index] = transcript.text
            st.success("Transkription gespeichert.")

    if st.session_state.transkriptionen[index]:
        st.subheader("📝 Transkription")
        st.write(st.session_state.transkriptionen[index])
        if st.button("➡️ Weiter zur nächsten Frage"):
            st.session_state.frage_index += 1

# Bewertung starten
if st.session_state.frage_index >= anzahl_fragen and not st.session_state.bewertung_abgeschlossen:
    st.subheader("✅ Alle Fragen beantwortet")
    if st.button("🧠 GPT-Bewertung starten"):
        st.session_state.bewertung_je_frage = []
        for i, (frage, antwort) in enumerate(zip(fragen, st.session_state.transkriptionen)):
            prompt = f"""
Du bist Fachprüfer:in für Kommunikation im Bildungsgang HF Betriebswirtschaft.

Bewerte die folgende mündliche Antwort nach diesen drei Kriterien (je 0–2 Punkte):
- Fachliche Relevanz
- Klarheit der Sprache
- Reflexionsfähigkeit

Gib eine Punktevergabe und einen kurzen Kommentar zur Antwort.

Frage: {frage}
Antwort: {antwort}
"""
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Du bist ein Kommunikationsexperte für HF-Prüfungen."},
                    {"role": "user", "content": prompt}
                ]
            )
            st.session_state.bewertung_je_frage.append(response.choices[0].message.content)
        st.session_state.bewertung_abgeschlossen = True

# Bewertung anzeigen
if st.session_state.bewertung_abgeschlossen:
    st.subheader("📊 GPT-Bewertung je Frage")
    for i, bewertung in enumerate(st.session_state.bewertung_je_frage):
        st.markdown(f"**Frage {i+1}: {fragen[i]}**")
        st.markdown(bewertung)
        st.markdown("---")
