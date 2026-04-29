> Django Technical Assessment - LogBook Text

# Fase 0: Voorwaarden + opstarten

Ik heb de opdracht ontvangen als vervolg op ons traject. Voor deze opdracht is in principe ongeveer 2 uur gepland; stap 1 bepaalt of er mogelijk iets meer nodig is. De opdracht is bewust ruim opgezet, waardoor het goed mogelijk is dat hij niet volledig afgerond wordt binnen de beschikbare tijd, en dat is prima. Op die manier is goed inzichtelijk hoe ver iemand komt met een gegeven tijdsbudget.

Belangrijk voor mij is niet alleen de code zelf, maar vooral ook het proces erachter. Daarom maak ik een logboek met de stappen die ik volg, de keuzes die ik maak, de prioriteiten die ik stel, de problemen die ik tegenkom en hoe ik ze oplos.

Een eenvoudige manier om dat bij te houden is een git-repository met regelmatige commits, maar een apart tekstbestand is ook prima. Ik kies hier voor het logboek-stijl, met een korte commitboodschap in de repository en de diepere technische details terug te vinden in de code per commit.

De eerste stap was inventariseren wat ik had ontvangen, wat er van mij wordt verwacht en hoe ik het project kan aanpakken.

Als experiment heb ik Google NotebookLM gebruikt om de originele opdracht te destilleren. Dat leverde goede vragen op en ik heb zelf enkele aanvullingen gedaan vanuit mijn ervaring met Laravel en frontend-ontwikkeling.

Ik heb dat vervolgens verwerkt in een 10-fasenplan dat overeenkomt met het origineel, maar met extra praktische tips en handvatten voor een soepelere start.

De eerste stap was het verkrijgen van de baseline in fase 1

-----------------------

## Phase 1: Baseline Setup & Reguliere Frontend (Tutorial 1-4)

### Algemene opdracht observatie

Het doel was om de officiële Django tutorial 1 t/m 4 zo nauwkeurig mogelijk te reconstrueren met Python 3.14 en Django 6.0. Daarmee ontstaat een stabiele basis voor de volgende fases: een werkende polls-app met de standaard tutorialstructuur, een goede ontwikkelworkflow en herhaalbare voorbeelddata.

### Kern onderdelen van deze opdracht

- Reconstructie van de tutorial-baseline in een standaard Django-project.
- Gebruik van Django Templates voor de frontend en Django Admin voor data-invoer.
- Opzetten van `Question` en `Choice` modellen met de bijbehorende views.
- Implementatie van `IndexView`, `DetailView`, `ResultsView` en de stemhandler.
- Eén dependency-/runtime-manager kiezen voor reproduceerbaarheid.
- Een seed-script toevoegen voor consistente voorbeelddata. (mijn toevoeging)

### Opties

- [bronkeuze]
  - De tutorial zelf stap voor stap volgen en de code handmatig opbouwen.
  - Een bestaande tutorial-app of git-repository zoeken.
  - AI gebruiken om de finale tutorialstatus te reconstrueren.

- [package-manager]
  - uv
  - pip / requirements.txt
  - poetry

- [database]
  - SQLite
  - PostgreSQL
  - MySQL

- [databeheer]
  - Django Admin gebruiken voor contentbeheer.
  - Zelf een extra formulierlaag bouwen.
  - Een seed-script toevoegen voor consistente ontwikkeldata.

### Gekozen opties

- [bronkeuze] AI gebruiken om de tutorial-baseline snel te reconstrueren; daarna de code handmatig verifiëren.
  - De gegenereerde tutorialcode controleren en waar nodig lokaal aanpassen.
- [package-manager] uv gebruiken als dependency- en runtime-manager.
- [database] SQLite gebruiken voor de database, omdat dit al in het tutorialproject is opgenomen, het direct werkt zonder externe service en het goed past bij een lokaal project.
  - PostgreSQL of MySQL zouden later ook eenvoudig inzetbaar zijn, maar in deze korte tijd wil ik niet te ver afwijken van de basis tutorialsetup.
- [databeheer] Django Admin inzetten voor management, met een seed-script voor consistente voorbeelddata.

### Waarom zijn deze opties gekozen

- [bronkeuze] AI als reconstructiemethode
  - Er was geen kant-en-klare tutorialversie beschikbaar die tegelijk aansloot op Python 3.14, Django 6.0 en de bestaande projectopzet.
  - AI gebruiken was daarom de snelste manier om een volledige baseline te reconstrueren en daarna handmatig te verifiëren.
  - De gegenereerde code is niet blind overgenomen: ik heb de output gecontroleerd tegen de officiële tutorial en lokaal aangepast waar nodig.

- [package-manager] uv als dependency- en runtime-manager
  - uv combineert Python-versioning, dependency management en een lockfile in één compacte tool.
  - `pip/requirements.txt` geeft minder zekerheid over reproduceerbaarheid, en `poetry` voegt extra tooling toe die in deze fase weinig oplevert.

- [database] SQLite als local-first database
  - SQLite werkt direct zonder externe service en past daardoor goed bij een compacte tutorial-baseline.
  - Voor deze fase is extra infrastructuur zoals PostgreSQL of MySQL vooral overhead; de models en views blijven inhoudelijk hetzelfde. (ondanks de installatie en het gebruik van de andere 2 database varianten niet heel complex is)
  - Latere migratie naar een zwaardere database blijft gewoon mogelijk als dat ooit nodig is.

- [databeheer] Django Admin met seed-script
  - Django Admin is voldoende voor deze fase, omdat de focus ligt op de tutorialstructuur en niet op een eigen beheerlaag.
  - Een custom formulierlaag zou onnodig veel tijd kosten en de scope van fase 1 vergroten.
  - Het seed-script maakt de ontwikkeldata met één commando reproduceerbaar beschikbaar.

### Problemen en oplossingen

- Er was geen kant-en-klare repository beschikbaar die exact Python 3.14, Django 6.0 en uv combineerde. Daarom is de tutorialstatus via een gerichte AI-aanpak nagebouwd en daarna gecontroleerd.
  - Ik heb Google AI Studio gebruikt om de officiële tutorialpagina’s te analyseren en de volledige codebasis te reconstrueren. De prompt beschreef expliciet dat ik een volledige markdown-output wilde met de finale file-structuur, uv-opstartcommando’s en complete Django-tutorialbestanden.
  - Dit werkte verrassend goed, even goed controleren, maar het werkt en best snel.
- Gezien de tutorial geen CRUD laag gaf voor het toevoegen van `Choices`, is een seed-script toegevoegd om consistente voorbeelddata snel te kunnen inladen.
  - In de tutorial gebruiken ze CLI commando's (shell) voor deze data.
- De uv-installatie is daarbij compleet gehouden met een lockfile (`uv.lock`) zodat de ontwikkelomgeving reproduceerbaar blijft en overeenkomt met de rest van het project.
  - O.a. de lockfile is pas in de volgende commit toegevoegd, deze was door mijn gekozen commando's niet gelijk aangemaakt.

-----------------------

## Phase 2: REST API Expositie

### Algemene opdracht observatie

Voeg een API-abstractie toe zodat we via REST zowel `Question` als `Choice` kunnen uitlezen en nieuw aanmaken.

### Kern onderdelen van deze opdracht

- Een REST API beschikbaar maken voor het `Question`-model.
- Een REST API toevoegen voor het `Choice`-model.
- Gebruik maken van DRF-serializers en viewsets voor standaard validatie en consistentie.
- Een duidelijke scheiding tussen HTML-routes en API-routes onder `/api/polls/`.
- Het `Question`-object direct werkend maken voor create/read.
- `Choice` als geneste actie toevoegen omdat een keuze altijd aan een specifieke vraag gekoppeld is.

### Opties

- [api-framework]
  - Native Django `JsonResponse` views bouwen.
  - Django REST Framework gebruiken met serializers en viewsets.

- [resource-model]
  - De huidige tutorialstructuur opsplitsen in twee echte top-level resources voor `Question` en `Choice`, zodat beide direct CRUD krijgen.
  - Het tutorialmodel behouden en het URL-model uitbreiden via een geneste structuur: `Choice` valt altijd onder `Question`.

- [route-structuur]
  - Alles onder één algemene endpointstructuur leggen.
  - API duidelijk scheiden met `/api/` prefix en nested routes voor relaties.

### Gekozen opties

- [api-framework]
  - Django REST Framework gebruiken met `ModelSerializer`, `ModelViewSet` en `DefaultRouter`.
- [resource-model]
  - Het originele tutorialmodel behouden; `Question` als hoofdresource implementeren en `Choice` via een extra `POST /api/polls/<id>/choices/` action toevoegen.
- [route-structuur]
  - API scheiden met een `/api/` prefix en nested routes voor de keuze-creatie.

### Waarom zijn deze opties gekozen

- [api-framework] Django REST Framework als API-standaard
  - DRF levert serializers, validatie en foutafhandeling uit de doos, waardoor je minder handmatig JSON-werk hoeft te schrijven.
  - Native `JsonResponse` zou hier meer boilerplate en meer kans op inconsistente foutafhandeling opleveren.
  - Zodra authenticatie, permissions en filtering meespelen, betaalt DRF zich pas echt terug.

- [resource-model] nested `Choice` onder `Question`
  - Een choice bestaat alleen in de context van een question; de URL-structuur moet dat ook laten zien.
  - Een losse top-level Choice-resource zou de domeinrelatie vertroebelen en een onrealistische API suggereren.
  - De nested opzet houdt het model logisch en maakt keuze-creatie expliciet gekoppeld aan een vraag.

- [route-structuur] `/api/`-prefix voor duidelijke scheiding
  - De scheiding tussen HTML en JSON wordt meteen duidelijk voor ontwikkelaars en gebruikers van de API.
  - Het helpt later ook bij uitbreiding van middleware, rate limiting en authenticatie per laag. (niet toegepast in dit project)
  - Het is een kleine wijziging met veel duidelijkheidswinst.

### Waarom deze viewset-logica er is in 'api_views.py'

```
class QuestionViewSet(viewsets.ModelViewSet):
```

In de API-viewset wordt onderscheid gemaakt tussen lijst- en detailverzoeken. Voor `retrieve` prefetchen we `choice_set` zodat de vraag met zijn keuzes in één keer geladen wordt, en gebruiken we een gedetailleerde serializer. Voor andere acties (hier list) houden we de query licht.

De `add_choice` custom action gebruikt `self.get_object()` om de juiste vraag te laden, valideert de binnenkomende keuze via `ChoiceSerializer`, en koppelt daarna de nieuwe keuze expliciet aan die vraag. Dit zorgt voor een veilige geneste endpointstructuur waarin keuzes altijd onder een specifieke vraag worden aangemaakt.

### Problemen en oplossingen

- In eerste instantie leek een DRF-viewset voor zowel `Question` als `Choice` te volstaan (idee), maar een losse top-level `Choice`-resource levert een ongemakkelijke URL-structuur op en ondermijnt de juiste ouder-kind binding.
  - Oplossing: `QuestionViewSet` gebruiken voor de hoofdresource en een custom action `choices` toevoegen voor choice-creatie.
- Zonder DRF moest veel JSON-parsing en foutafhandeling handmatig worden gedaan.
  - Oplossing: overstappen op DRF voor standaard serializers en `ModelViewSet`-gedrag. Veel wordt dan al voor je gedaan.

### Vragen

- (real) In de bespreking zal ik vragen hoe je bepaalt wat er in deze API komt aan functies en data, en waarom je jouw aanpak hebt gekozen.
  - Antwoord: Ik kies functies en data op basis van de bestaande domeinrelaties in het tutorialmodel. `Question` is de hoofdresource met volledige create/read-ondersteuning omdat dat rechtstreeks bij het probleem past, terwijl `Choice` een geneste actie krijgt omdat keuzes altijd onder een vraag horen. Dit levert een heldere, onderhoudbare API zonder onnodige losse top-level resources.
- (added) Hoe zorg je ervoor dat de API uitbreidbaar blijft zonder het huidige tutorialmodel te breken?
  - Antwoord: Door het bestaande `Question`/`Choice`-model te behouden en alleen de API-laag te bouwen, houd ik de domeinlogica stabiel. Nieuwe features kunnen later worden toegevoegd via extra actions of nested endpoints zonder onderliggende databasemodellen te veranderen.
- (added) Waarom heb je gekozen voor een nested `choices`-endpoint in plaats van een losse `ChoiceViewSet`?
  - Antwoord: Omdat `Choice` alleen zinvol is in de context van een `Question`, voorkomt een nested endpoint onduidelijke URL’s en mogelijke parent-child confusie. Dit maakt de resource-relatie expliciet in de API en voorkomt dat een keuze zonder vraag kan bestaan.
- (added) Welke voordelen geeft DRF in deze fase ten opzichte van een custom JsonResponse-oplossing?
  - Antwoord: DRF levert directe validatie, foutafhandeling, serializers en viewset-logica zonder deze zelf te bouwen. Dat versnelt de implementatie en maakt de API robuuster, terwijl de huidige applicatiestructuur behouden blijft.

### Flow

- URL > request > question (CRUD) / choice (action:post) > view > serializer (validator) > [business logic] > serializer (response)

- business logic
  - simpel (request, validate, save, response)
  - custom (request, validate, [custom+save], response)

-----------------------

## Phase 3: Celery Achtergrondtaak

### Algemene opdracht observatie

Het doel van deze fase is duidelijk: aantonen dat je een echte Celery-achtergrondtaak kunt opzetten en laten draaien. De opdracht vraagt expliciet om een periodieke taak die automatisch nieuwe `Question`-objecten met meerdere `Choice`-records aanmaakt. De inhoud van die data mag eenvoudig en willekeurig zijn; de taak zelf en de Celery-configuratie zijn het belangrijkste.

### Kern onderdelen van deze opdracht

- Celery integreren in het Django-project.
- Een broker kiezen en configureren voor task dispatch.
- Een periodieke taak definiëren die elk uur een nieuwe vraag met keuzes maakt.
- De scheduling in Celery Beat vastleggen.
- Redis lokaal beschikbaar maken als broker service.
- De minimale opzet documenteren, zodat iemand anders de stack kan starten.

### Opties

- [broker-keuze]
  - Celery met Redis als broker.
  - Celery met RabbitMQ als broker.

- [scheduler-keuze]
  - Celery Beat via `CELERY_BEAT_SCHEDULE` in Django settings.
  - `django-celery-beat` of een database-backed scheduler.

- [data-generatie]
  - Simpele mock-data generator met standaardbibliotheek.
  - Extra dependency zoals Faker gebruiken.

- [service-opzet]
  - Redis lokaal via Docker container.
  - Redis handmatig of via een andere service opzetten.

### Gekozen opties

- [broker-keuze]
  - Celery met Redis als broker.
- [scheduler-keuze]
  - Celery Beat via `CELERY_BEAT_SCHEDULE` in de settings.
- [data-generatie]
  - Simpele mock-data generator met standaardbibliotheek.
- [service-opzet]
  - Redis lokaal via een Docker helper script.

### Waarom zijn deze opties gekozen

- [broker-keuze] Redis vs RabbitMQ
  - Redis is sneller op te zetten en minder gevoelig voor installatieproblemen in een korte assessmentcontext.
  - RabbitMQ is een sterke broker, maar vraagt meer configuratie en levert hier geen extra bewijswaarde op.
  - Voor deze fase wil ik vooral Celery laten zien, niet een apart brokerproject opzetten.

- [scheduler-keuze] statische Beat-schedule vs `django-celery-beat`
  - Eén vaste hourly taak vraagt geen database-backed scheduler of admininterface.
  - `CELERY_BEAT_SCHEDULE` is direct, overzichtelijk en voldoende om de planning aantoonbaar te maken.
  - `django-celery-beat` zou extra modellen, migraties en beheer toevoegen zonder praktische winst voor deze opdracht.

- [data-generatie] standaardbibliotheek vs Faker
  - De taak heeft alleen eenvoudige testdata nodig; daarvoor is de standaardbibliotheek genoeg.
  - Faker voegt extra afhankelijkheden en configuratie toe zonder dat de kern van de Celery-opdracht sterker wordt.
  - Minder dependencies betekent minder onderhoud en minder kans op ruis in de demo.

- [service-opzet] Docker-backed Redis
  - Een container maakt de lokale Redis-start reproduceerbaar op verschillende machines.
  - Handmatige installatie verschilt te veel per platform en kost in een assessment onnodig veel tijd.
  - Het helper script houdt de setup compact en makkelijk te herhalen.

### Problemen en oplossingen

- De outputdata mag willekeurig zijn, maar de taak moet wel valide Django-modellen maken.
  - Oplossing: een vaste lijst prefixes en choice-labels gebruiken, aangevuld met een timestamp, zodat de task altijd bruikbare records aanmaakt.
- Als Redis niet draait, faalt de Celery worker direct.
  - Oplossing: een `redis.sh` helper toevoegen die een lokale Redis-container start of bestaande container herstart. Hier bovenop tests maken zodat we daadwerkelijk de 'task' testen.

### Vragen

- (real) Hoe bewijs ik dat de taak zelf werkt en dat de Celery-configuratie juist is?
  - Antwoord: door de taskmodule in `polls/tasks.py` te laten draaien via een Celery worker en Celery Beat te gebruiken voor de hourly scheduling; in de bespreking laat ik zien dat de broker, worker en scheduler samenwerken. Of de 1 minuut variant activeren, voor een snelle check.
- (real) Waarom kies je Redis als broker in plaats van RabbitMQ?
  - Antwoord: Redis start sneller en vraagt minder setup in een tijdsgebonden assessment, terwijl het wel dezelfde Celery-architectuur laat zien.
- (added) Waarom gebruik je geen `django-celery-beat`?
  - Antwoord: omdat de opdracht een statische hourly taak vraagt; de extra database scheduler zou alleen meer complexiteit toevoegen zonder waarde.
- (added) Hoe start een beoordelaar de Celery stack lokaal?
  - Antwoord: met `bash redis.sh` voor Redis, daarna `uv run celery -A mysite worker -l info` en `uv run celery -A mysite beat -l info` in de `djangotutorial`-directory.
- (added) Welke onderdelen van de Celery-keten zijn belangrijk om te benoemen in de bespreking?
  - Antwoord: broker URL, task discovery, `CELERY_BEAT_SCHEDULE`, worker-executie en de periodic task zelf.

-----------------------

## Phase 4: Test Strategie

### Algemene opdracht observatie

Het doel van deze fase is om een teststrategie te kiezen en een kleine, praktische testset toe te voegen die de belangrijkste risico’s van de polling-app en API afdekt. Het gaat niet om zoveel mogelijk tests, maar om de juiste tests voor de belangrijkste gebruikersflows, de API-contracten en de achtergrondtaak.

### Kern onderdelen van deze opdracht

- Bepalen welke functionaliteit echte regressies veroorzaakt als het faalt.
- Kiezen tussen een eenvoudige Django-teststack en een uitgebreidere `pytest`-opzet.
- Beslissen welke laag van de app het meest waardevol is om te testen: model, view, API en/of Celery.
- Prioriteren van testdekking op basis van tijd en risico.

### Opties

- [test-framework]
  - Django `TestCase` gebruiken zonder extra configuratie.
  - `pytest-django` inzetten met fixtures en marker-structuur.

- [scope-keuze]
  - brede coverage proberen te halen met zoveel mogelijk voorbeelden.
  - gerichte coverage voor de high-stakes flows.

- [test-laag]
  - alleen model- en viewtests schrijven.
  - ook API- en Celery-tasktests opnemen.

### Gekozen opties

- [test-framework]
  - Django `TestCase` gebruiken voor een zero-config benadering.
- [scope-keuze]
  - gefocuste coverage op de meest kritieke use cases.
- [test-laag]
  - model-, view-, API- en Celery-tests opnemen.

### Waarom zijn deze opties gekozen

- [test-framework] Django `TestCase` vs `pytest-django`
  - `TestCase` is ingebouwd, direct inzetbaar en vraagt geen extra testconfiguratie.
  - `pytest-django` is krachtiger, maar de extra setup en pluginlaag voegen in deze kleine suite weinig toe.
  - Voor een compacte, gerichte testsuite is eenvoud hier belangrijker dan toolingrijkdom.

- [scope-keuze] gefocuste coverage
  - De tests richten zich op de onderdelen die echt kapot kunnen gaan: stemflow, API-contracten, modelgedrag en Celery.
  - Frameworkdetails zoals Django's `reverse()` of DRF's parsing test ik niet opnieuw; die zijn al door het framework afgedekt.
  - Zo blijft de suite klein, relevant en onderhoudbaar.

- [test-laag] model, view, API en Celery
  - Alleen modeltests zouden de HTTP- en API-flow niet afdekken.
  - Alleen integrationtests zouden kleine maar belangrijke domeinregels missen.
  - Door ook de Celery-taak te testen, vang ik stille regressies in de achtergrondautomatisering vroeg op.

### Tests uit fase 4

- Een compacte set tests is toegevoegd voor de kernflows: modellogica, stemactie, API-detail en choice-creatie.
  - `test_models.py::QuestionModelTests::test_was_published_recently_returns_true_for_recent_question`
  - `test_views.py::VoteViewTests::test_vote_creates_user_vote_and_increments_choice_votes`
  - `test_api.py::PollsApiTests::test_api_question_detail_returns_nested_choices`
  - `test_api.py::PollsApiTests::test_api_add_choice_creates_choice_for_question`
- Een extra guard test voor de Celery-taak toegevoegd om stil falende achtergrondautomatisering vroeg te detecteren.
  - `test_tasks.py::CeleryTaskTests::test_create_hourly_question_creates_question_and_choices`
- Deze tests beschermen de meest risicovolle onderdelen in deze fase zonder onnodige frameworkdetails te testen.

### Waarom deze tests

- Deze selectie volgt een risico-gedreven aanpak: we willen minimale testdekking die maximaal beschermt.
- `test_models.py :: test_was_published_recently_returns_true_for_recent_question` dekt modellogica en zorgt dat de kerndomeinregel over recente vragen betrouwbaar blijft.
- `test_views.py :: test_vote_creates_user_vote_and_increments_choice_votes` dekt de kritieke stemflow en de belangrijkste bijwerkingen van een stemactie.
- `test_api.py :: test_api_question_detail_returns_nested_choices` controleert dat de API-detailresponse de relevante gerelateerde data teruggeeft zonder dat de frontend daar extra queries voor hoeft te doen.
- `test_api.py :: test_api_add_choice_creates_choice_for_question` valideert de geneste create action en bevestigt dat choices altijd aan de juiste vraag worden gekoppeld.
- De `Celery` guard test is toegevoegd omdat achtergrondtaken geen directe gebruikerfeedback geven, maar wel stil kunnen falen; die test vangt zulke regressies vroeg.
- Samen vormen deze tests een balans tussen domeinlogica, HTTP/API-contracten, en achtergrondautomatisering, zonder meer framework-internaliteit te testen dan nodig.

### Tests toegevoegd na deze fase

- Twee andere voorbeeldien hoge-impact tests die sindsdien belangrijk zijn gebleven (edge / negative tests):
  - `test_api.py::PollsApiVoteTests::test_api_vote_rejects_invalid_choice` — een vote-edgecase test die kiest voor een mismatch tussen vraag en keuze om verkeerde stemregistratie te voorkomen.
  - `test_api.py::PollsApiVoteTests::test_api_vote_rejects_anonymous_user` — een auth-guard test die bevestigt dat anonieme gebruikers geen stem kunnen uitbrengen.
- De basisset is later opgesplitst en uitgebreid in losse testmodules, zodat nieuwe functionaliteit makkelijker een eigen testlaag krijgt.
- Hierdoor is de huidige suite duidelijker: modeltests staan naast viewtests, API-tests en taaktests, in plaats van één lang bestand.
- Een gebruikersgerichte test toegevoegd voor login-gedrag: zonder ingelogde gebruiker mogen keuzes niet zichtbaar zijn en stemmen niet mogelijk zijn.

### Problemen en oplossingen

- Te veel tijd verliezen aan low-value tests of framework details.
  - Oplossing: focus op eigen domeinlogica en publieke contracten, laat Django/DRF internals aan het framework zelf over.
- Stille fouten in de Celery-automatisering missen.
  - Oplossing: extra guard tests voor `create_hourly_question` (en de snelle smoke-task) met voorspelbare mockdata.

### Vragen

- (real) In de bespreking zal ik vragen hoe je kiest welke aspecten je tests voor schrijft, hoe de tests zelf werken, en hoe je valideert dat de tests compleet zijn.
  - Antwoord: ik gebruik een risico-gebaseerde keuze: test de kritieke gebruikersflows, public API contracten en eigen domeinlogica; laat low-risk frameworkdetails aan Django/DRF over.
- (added) Waarom kies je Django `TestCase` in plaats van `pytest-django`?
  - Antwoord: het is zero-config, sluit direct aan op de bestaande repository zonder extra dependencies en is sneller in te zetten in deze fase.
- (added) Waarom test je ook Celery-taken in deze fase?
  - Antwoord: de achtergrondtaak kan stil falen zonder dat de webinterface direct breekt, dus dat is een hoog-risico onderdeel dat extra bewaking verdient.
- (added) Waarom schrijf je geen tests voor elk Django- of DRF-detail?
  - Antwoord: die frameworkonderdelen zijn al getest door hun eigen teams; hier bescherm ik vooral onze eigen applogica en de integratiepunten die we zelf bouwen.

-----------------------

## Phase 5: Gebruikersacties Vastleggen (Individuele stemmen)

### Algemene opdracht observatie

De opdracht is om individuele stemmen vast te leggen, niet alleen een stemteller. Dat betekent dat we per gebruiker moeten kunnen bijhouden op welke `Choice` is gestemd en dat een gebruiker maximaal één keer per `Question` stemt.

### Kern onderdelen van deze opdracht

- kiezen tussen alleen een teller (wel of niet behouden), een impliciete m2m-relatie of een expliciet stemmodel
- de businessregel afdwingen: één stem per gebruiker per vraag
- metadata zoals het tijdstip van stemmen kunnen bewaren
- anonieme gebruikers niet toestaan om te stemmen
- bestaande UI en tests klein houden voor deze fase

### Opties

- [opslag-structuur]
  - alleen `Choice.votes` gebruiken als teller
  - een standaard `ManyToManyField` tussen user en choice gebruiken
  - een expliciet `UserVote` model met eigen metadata maken
    - (3 FK's en een datum veld : choice_id, question_id, user_id, created_at)

- [cache-strategie]
  - `Choice.votes` verwijderen en later berekenen uit `UserVote`
  - `Choice.votes` behouden als compatibele lees-cache

- [unieke-regel]
  - alleen in de view afhandelen
  - in de database dwingen met een unieke constraint op `user + question`
    - expliciet `question` opnemen op `UserVote` voor een directe modelinvariant

- [gebruikersflow]
  - anonieme stemming toestaan
  - anonieme stemming blokkeren en aandacht geven aan login

### Gekozen opties

- [opslag-structuur]
  - kies een expliciet `UserVote` model
- [cache-strategie]
  - kies `Choice.votes` te behouden als compatibele lees-cache
- [unieke-regel]
  - kies een databaseconstraint op `user + question`
- [gebruikersflow]
  - anonieme stemmen blokkeren en een login hint tonen

### Waarom zijn deze opties gekozen

- [opslag-structuur] expliciet `UserVote`-model
  - Van het 'voten' zelf een expliciet domeinobject maken is duidelijker dan alleen een verborgen join-tabel of alleen een teller.
  - Het model kan metadata zoals gebruiker, keuze, vraag en tijdstip direct opslaan.
  - Daarmee blijft de stemlogica goed afleesbaar, uitbreidbaar en goed toetsbaar.

- [cache-strategie] `Choice.votes` behouden
  - De bestaande UI en resultatenpagina blijven daardoor ongewijzigd werken.
  - Alles in één keer ombouwen naar berekende waarden zou deze fase onnodig groot en risicovol maken.
  - De echte bron van de stemgegevens ligt in `UserVote`; `Choice.votes` blijft voorlopig alleen een compatibele cache. (ombouwen hiervan was geen onderdeel van de opdracht, tijdrovend en berekende velden kwamen terug in een volgende fase)

- [unieke-regel] databaseconstraint
  - De database moet de regel afdwingen, niet alleen de view.
    - De extra `question`-kolom op `UserVote` is geen redundantie, maar een bewuste keuze om de `user + question` constraint direct en robuust in het datamodel vast te leggen.
  - Daarmee voorkom je racecondities en directe writes die de businessregel zouden omzeilen.
  - De view blijft verantwoordelijk voor een nette gebruikerservaring, maar de integriteit ligt op dataniveau.

- [gebruikersflow] anonieme stemmen blokkeren
  - Zonder login kun je niet betrouwbaar garanderen dat één persoon maar één keer stemt.
  - Door anonieme stemmen te blokkeren, sluit de flow aan op de databaseconstraint per gebruiker en vraag.
  - De loginhint in de UI maakt dat gedrag meteen begrijpelijk.

### Testen

- In de codebase bestaan view-variant tests met expliciete testnamen zoals:
  - `test_views.py::VoteViewTests::test_vote_creates_user_vote_and_increments_choice_votes`
  - `test_views.py::VoteViewTests::test_vote_rejects_second_vote_from_same_user_on_same_question`
  - `test_views.py::VoteViewTests::test_vote_rejects_anonymous_user`
- De API-variant wordt aangevuld door gerelateerde tests in `djangotutorial/polls/tests/test_api.py`, zodat de oplossing zowel de publieke JSON-contracten als de bestaande HTML-voteflow afdekt.
- Samen zorgen deze testlagen ervoor dat de nieuwe per-gebruiker stemlogica goed beschermd wordt zonder brede refactor van de bestaande UI of resultatenpagina.

### Performance

- De nieuwe `UserVote`-tabel blijft binnen de scope performant door de unieke businessregel te ondersteunen met een databaseconstraint op `(user, question)`. Dat is functioneel en wordt door de database ook fysiek versneld via een index.
- `ForeignKey`-velden naar `User`, `Question` en `Choice` zorgen ervoor dat de belangrijkste zoekpaden standaard gebruikmaken van onderliggende indexen. Hierdoor blijven lookups voor bestaande stemmen en gerelateerde objecten efficiënt.
- We kiezen er in Phase 5 nog niet voor om `Choice.votes` om te bouwen tot een berekende aggregatie. Het blijft een compatibele cache.
  - Dat betekent wel dat we tijdelijk twee schrijfpunten hebben: bij elke stem moet zowel `UserVote` als de cached `Choice.votes` worden bijgewerkt. Dat is minder efficiënt dan één enkele realtime berekening en brengt een extra consistentierisico met zich mee als de update-logica later verandert.
  - Voor nu is dat acceptabel omdat de stemservice / `vote()`-flow is ontworpen met een `transaction.atomic()`-context, zodat een `UserVote` en de bijbehorende tellerupdate samen worden weggeschreven. De belangrijkste paden zijn ook gedekt door tests voor zowel succesvolle stemmen als dubbele of anonieme stemmen.
  - In een productieomgeving is het daarom goed om later te vergelijken wat het beste werkt: een realtime berekening met annotaties of een cache-gedreven aanpak die vooral nuttig is als de reads echt een bottleneck blijken.
  - En verder dat de huidige tijdelijk variant (dubbel opslaan, als rijen en als berekende cache) te complex/foutgevoelijg is.
- Deze aanpak houdt het project binnen de scope: we voorkomen duplicate vote checks en bewaken de schaalbaarheid van de nieuwe modelstructuur, zonder meer te doen dan nodig voor deze fase.

### Problemen en oplossingen

- Wel of niet `Choice.votes` behouden als cache of die helemaal weghalen.
  - Oplossing: `Choice.votes` blijft voorlopig bestaan als compatibele cache. Het is vooral handig voor leesgebruik, terwijl de echte gebruikersstemmen in `UserVote` verdwijnen. De afhandeling van berekende velden blijft voor Phase 6, zodat Phase 5 niet onnodig complex wordt.
- De dubbele aanwezigheid van `question` in zowel `Choice` als `UserVote` voelde aanvankelijk overbodig.
  - Oplossing: dit is een bewuste ontwerpkeuze om de `user + question` invariant direct in het model te kunnen leggen en daardoor een robuuste databaseconstraint te ondersteunen.

### Vragen

- (real) Welke architectuurkeuzes heb je overwogen voor het vastleggen van individuele stemmen, en waarom koos je voor een expliciet `UserVote` model met een databaseconstraint?
  - Antwoord: we hebben alleen een teller (welke er al was), een standaard `ManyToManyField` en een expliciet model overwogen. Het expliciete model ondersteunt metadata, maakt de relatie duidelijker en stelt ons in staat om met een databaseconstraint `één gebruiker, één stem per vraag` te garanderen.
- (added) Hoe bewijs je in deze fase dat gebruikersacties echt los worden opgeslagen?
  - Antwoord: door het expliciete `UserVote` model met `user`, `choice`, `question` en `created_at` te gebruiken en tests toe te voegen voor succesvolle stemmen en dubbele stemmen.
- (added) Waarom houd je `Choice.votes` nog steeds aan?
  - Antwoord: omdat het de bestaande UI stabiel houdt en deze fase primair gaat over individuele opslag, niet over het volledig vervangen van alle aggregatie.
- (added) Waarom geen `ManyToManyField` met een through-model?
  - Antwoord: een expliciet model maakt de intentie duidelijker in de code en is makkelijker te bespreken; het voorkomt dat de join-tabel verborgen blijft.
- (added) Waarom is een databaseconstraint belangrijker dan alleen viewlogica?
  - Antwoord: omdat de constraint hard afdwingt dat een gebruiker niet twee keer op dezelfde vraag kan stemmen, zelfs bij racecondities of onvoorziene requestpaden.
- (added) Welke foutpaden test je specifiek?
  - Antwoord: anonieme stempogingen, dubbele stemmen en het kiezen van een `Choice` die niet bij de huidige vraag hoort.

-----------------------

## Phase 6: Efficiënte Berekende Waardes

### Algemene opdracht observatie

Het doel is een berekende waarde toe te voegen aan het top-model `Question`, namelijk het aantal gerelateerde `Choice`-objecten, en dit op een efficiënte manier te doen zodat de lijstpagina niet terugvalt op een N+1-querypatroon.

### Kern onderdelen van deze opdracht

- Maak het aantal gerelateerde `Choices` beschikbaar op de `Question`-lijst.
- Bereken die waarde in de database, niet in Python per object.
- Houd de scope beperkt tot de lijstweergave en de getoonde count in de template.
- Bescherm de oplossing met tests voor correcte uitkomst en query-efficiëntie.

### Opties

- [query-optie]
  - `annotate(choice_count=Count('choice'))` gebruiken op de queryset
  - `@property` of modelmethode gebruiken om het aantal choices te tellen
  - `prefetch_related()` gebruiken en daarna in Python tellen
  - een custom manager/queryset helper toevoegen voor herbruikbare annotatie

- [data-opslag-cache]
  - een extra persistente kolom gebruiken
    - een extra opgeslagen kolom op `Question` gebruiken en die synchroniseren
  - alleen de bestaande relationele count laten berekenen

- [scope]
  - alleen de HTML-lijst aanpassen
  - ook de API-serializers uitbreiden
  - een bredere refactor naar een reusable manager doen

### Gekozen opties

- [query-optie]
  - kies `annotate(choice_count=Count('choice'))` op de queryset
- [data-opslag-cache]
  - kies alleen de relationele count te berekenen, geen extra opgeslagen veld
- [scope]
  - kies de aanpassing te beperken tot de HTML-lijstpagina

### Waarom zijn deze opties gekozen

- [query-optie] `annotate()` op de queryset
  - De database kan de count efficiënter berekenen dan Python per object.
  - Een property met `choice_set.count()` zou per rij extra queries veroorzaken en dus een klassiek N+1-probleem geven.
  - `prefetch_related()` haalt meer data op dan nodig is als je alleen het aantal wilt tonen.
  - Een custom manager is pas interessant als meerdere views dezelfde annotatie nodig hebben; voor nu is een gerichte queryset-oplossing eenvoudiger.

- [data-opslag] geen extra opgeslagen kolom
  - Een opgeslagen count-kolom vraagt om synchronisatie bij elke wijziging en introduceert risico op verouderde data.
  - De relationele count is hier betrouwbaar genoeg en makkelijker te onderhouden.
  - Door alleen te rekenen in de query blijft het model simpel.

- [scope] alleen de HTML-lijstpagina
  - De fase vraagt om een efficiënte lijstweergave, niet om een volledige API-herbouw.
  - De bestaande templates blijven bruikbaar, waardoor de wijziging klein en gecontroleerd blijft.
  - De API kan later dezelfde logica overnemen als daar een concrete behoefte voor ontstaat.

### Testen

- In de codebase bestaat een testklasse voor de lijstweergave met expliciete testnamen zoals:
  - `test_views.py::QuestionListViewTests::test_index_view_shows_annotated_choice_count`
  - `test_views.py::QuestionListViewTests::test_index_view_uses_one_query_for_multiple_questions`
  - `test_views.py::QuestionListViewTests::test_annotated_choice_count_defaults_to_zero`
- Deze tests bewaken zowel de functionele uitkomst als het query-gedrag.
- Samen zorgen deze testlagen ervoor dat de berekende `choice_count` juist en efficiënt beschikbaar is zonder brede refactor van de GUI of API.

### Performance

- Phase 6 is bedoeld als een performance test: we laten zien dat de lijstweergave op het top-model efficiënt kan rekenen, niet alleen dat de waarde functioneel klopt.
- `annotate(choice_count=Count("choice"))` is hier de kern: de telling gebeurt in de database, niet in de template of met een `@property` per object.
- Deze fase bewijst dat één geannoteerde query genoeg is voor meerdere vragen, en voorkomt het klassieke N+1-patroon waar elke vraag een extra count-query triggert.
- We houden het doelgericht: geen denormalisatie, geen extra cache, geen extra managerlaag. De performanceverbetering blijft beperkt tot de lijstweergave en de geannoteerde queryset.

### Problemen en oplossingen

- De neiging om het aantal choices via een `@property` op het model te berekenen is groot omdat het compact lijkt.
  - Oplossing: erkennen dat dit in een lijstweergave per rij een extra query triggert; queryset-annotatie in de view is duidelijker en efficiënter.
- Het is verleidelijk om meteen een reusable manager op te zetten of een denormalized kolom toe te voegen voor toekomstige fasen.
  - Oplossing: beperken tot de lijstweergave en tellen in de query; manager-abstractie en opgeslagen velden kunnen Phase 7 wachten als de behoefte bewezen is.
- De opdracht vraagt om efficiëntie, dus regressie naar extra queries moet worden gevangen.
  - Oplossing: test met een `assertNumQueries(1)`-case voor meerdere vragen en choices.

### Vragen

- (real) Welke risico's zie je voor inefficiëntie, hoe ga je daarmee om, en hoe controleer je dat jouw aanpak werkt?
  - Antwoord: het risico is dat een `@property` op `Question` per rij een extra query triggert. Ik controleer dit met een `assertNumQueries(1)`-test in de lijstweergave en ga dat tegen door `annotate()` op de queryset te gebruiken.
- (added) Waarom geen extra opgeslagen `choice_count`-veld?
  - Antwoord: een opgeslagen veld vereist synchronisatie bij elke wijziging en introduceert stale-data risico's. Voor deze fase is rekenen in de query eenvoudiger en betrouwbaarder.
- (added) Waarom niet direct een custom manager gebruiken?
  - Antwoord: een custom manager is waardevol als meerdere views dezelfde annotatie delen. Voor deze fase is de wijziging beperkt tot één lijstview en houd ik het daarom eenvoudig.
- (added) Hoe houd je de scope klein en risico's laag in deze fase?
  - Antwoord: door alleen de lijstpagina aan te passen en de bestaande template te hergebruiken. De API en andere delen blijven ongemoeid totdat er bewijs is dat ze ook dezelfde berekende waarde nodig hebben.
- (added) Waarom pas je de API in deze fase niet gelijk aan met dezelfde annotatie?
  - Antwoord: Phase 6 vraagt om berekening op het top-model in de HTML-weergave; API-uitbreiding hoeft niet nu. Later moet dezelfde queryset-annotatie-regel wel gelden om N+1 ook daar te voorkomen. maar vooral -> Om tijd redenen en met de weet van de volgende fase heb ik dit even doorgeschoven.

-----------------------

## Phase 7: API-gedreven Frontend Pagina (round 1,2,3)

### Algemene opdracht observatie

De opdracht is om naast de bestaande reguliere Django-frontend een nieuwe pagina te bouwen die volledig via de REST API communiceert. Die pagina moet vragen ophalen, details tonen, stemmen verzenden en uiteindelijk choices beheren zonder normale Django-formulieren of template-posts.

Fase 7 is opgedeeld in drie concrete stappen:

1. eerst een basis API-front-end voor stemmen en vragen
2. daarna choice create/update via REST
3. tenslotte choice delete.

Het doel is aantoonbaar te maken dat deze app niet alleen server-rendered kan werken, maar ook als een lichtgewicht, API-gedreven interface.

### Kern onderdelen van deze opdracht

- bouw een aparte API-driven frontendpagina naast de bestaande tutorialpagina’s
- kies een minimale frontendaanpak die JSON via de DRF API kan lezen en schrijven
- behoud de bestaande Django session auth en CSRF-veiligheid
- implementeer stemmen via `POST /api/polls/<id>/vote/`
- voeg delete toe voor choices in de laatste stap
- zorg dat de keuzegegevens en question list 'state', na writes vers blijven
- breid de API/frontend uit met choice create/update
  - ik koos hier voor 'choice' gezien het meer expressief is (bewerkingen hebben direct een duidelijk effect op de antwoorden lijst, het vast zetten van een antwoord wanneer je al een 'vote' hebt gedaan, verwijderen en weer kunnen voten, antwoorden kan je verwijderen zonder hierbij je 'main holder question' te verliezen en verder goed en duidelijk te presenteren in de frontend view en later audit tab)
  - 'questions' had ook gekund, maar is ook al aanwezig in de admin backend

### API frontend URL-structuur vervolg

In Phase 2 hebben we al besloten om het datamodel te volgen: `Question` staat centraal en `Choice` is altijd onderdeel van een vraag. In Phase 7 zetten we diezelfde structuur door in de API frontend. De routes zijn daarom zo ingericht dat acties op keuzes altijd onder een vraag plaatsvinden, bijvoorbeeld `POST /api/polls/<question_id>/choices/` voor het toevoegen van een nieuw antwoord.

Dat maakt de URL-structuur voorspelbaar en consistent met het domein: een `Choice` bestaat in deze applicatie niet los van een `Question`. Het helpt ook om authorisatie en validatie eenvoudig te houden, omdat de viewset eerst de juiste `Question` laadt en daarna pas de `Choice`-bewerking uitvoert.

### Opties

- [frontend-framework]
  - Alpine.js via CDN
  - Vanilla JavaScript met `fetch()` zonder framework
  - HTMX met server-rendered HTML-fragmenten
  - React/Vue met build tooling

- [api-scope]
  - alleen stemmen ondersteunen via de API
  - extra choice create/update/delete toevoegen
  - de hele app naar een API-only frontend migreren

- [authenticatie]
  - Django session auth + CSRF
  - token- of JWT-authenticatie

- [auth-strategie]
  - Handmatige logincheck in elke methode.
  - `@permission_classes([IsAuthenticated])` per actie.
  - Geclusterde permissions via `get_permissions()` op viewsetniveau.

- [state-management]
  - inline script in de template
  - aparte statische JS/CSS assets
  - geen geselecteerde-choice state meenemen

- [code-structure]
  - duplicate vote- en choice-logica in HTML/API separaat houden
  - een shared `polls/services.py` vote-service gebruiken
  - volledig aparte implementaties per route handhaven

- [data-model]
  - choice count als query-annotatie laten berekenen
  - choice votes als compatibele cache behouden
  - user_choice_id toevoegen voor de gekozen optie
  - verse queryset per API-request gebruiken
  - shared `QuestionManager`/`QuestionQuerySet` helper voor `with_choice_count()` en `with_choices()`

### Gekozen opties

- [frontend-framework]
  - Alpine.js via CDN
- [api-scope]
  - begin met stemmen en vraag details, breid daarna choice create/update uit, en voeg in ronde 3 delete toe
- [authenticatie]
  - Django session auth met SessionAuthentication en CSRF
- [auth-strategie]
  - Kies voor geclusterde permissions via `get_permissions()` in de viewset.
- [state-management]
  - origineel inline JavaScript starten, later refactoren naar externe `api_frontend.js` en `api_frontend.css`
- [code-structure]
  - shared `polls/services.py` gebruiken om vote- en choice-logica te delen tussen HTML en API
  - voor zowel view als API dezelfde backendregels laten gelden
- [data-model]
  - choice count via SQL-annotatie berekenen
  - `Choice.votes` behouden als compatibele cache (dit meer om tijd redenen en fase/project scope, maar dit was wel een mooi moment geweest om dit om te bouwen)
  - `user_choice_id` toevoegen in detail payloads voor de geselecteerde keuze
  - per request verse querysets gebruiken om stale API-data te voorkomen
  - gedeelde `QuestionManager`/`QuestionQuerySet` helper gebruiken om annotate/prefetch-logica te centraliseren

### Waarom zijn deze opties gekozen

- [frontend-framework] Alpine.js via CDN
  - Alpine.js geeft reactiviteit zonder bundler, Node.js-installatie of build-stappen.
  - Vanilla JavaScript zou hier snel onoverzichtelijk worden zodra loading, error-states en selectiegedrag tegelijk spelen.
  - HTMX past minder goed, omdat deze fase juist JSON via de DRF API gebruikt in plaats van server-gerenderde fragments.
  - React of Vue zouden technisch kunnen, maar brengen veel extra setup mee voor een relatief lichte API-consumer.
  - Alpine.js is daardoor niet de beste oplossing, maar wel de meest passende.

- [api-scope] progressieve uitbreiding
  - In de eerste ronde staan stemmen en vraagdetail centraal, omdat dat het kerngebruik is.
  - Daarna volgen choice create en update zodat de API ook schrijfacties dekt.
  - De delete-stap maakt het CRUD-patroon compleet en laat zien dat de UI incrementeel is opgebouwd.
  - Deze volgorde houdt de scope per stap beheersbaar.
  - Een volledig ombouw vond ik buiten scope, het demonstreren van duidelijk onderdelen (vote + choice CRUD) matcht wat betreft tijd en output het beste bij de vraag

- [authenticatie] session auth + CSRF
  - De app draait al op Django sessions, dus extra authlagen zijn niet nodig.
  - SessionAuthentication past direct bij gebruik op dezelfde origin en houdt CSRF-beveiliging intact.
  - Token- of JWT-authenticatie zou hier vooral extra beheer en complexiteit toevoegen.

- [auth-strategie] geclusterde permissions via `get_permissions()`
  - Mijn voorkeur gaat uit naar één centrale plek voor de write-permissions, omdat de beveiliging dan direct naast de rest van de viewsetlogica staat.
  - De handmatige logincheck in elke methode werkt wel, maar mengt security met businesslogica en maakt het makkelijker om een check te vergeten.
  - `@permission_classes([IsAuthenticated])` per actie is prima als een viewset later wordt opgedeeld of veel losse acties krijgt; dan blijft de beveiliging lokaal zichtbaar.
  - In deze fase wil ik vooral alles rondom choice-writes overzichtelijk op één plek houden, dus `get_permissions()` past hier het best.

- [state-management] inline code naar externe assets
  - De eerste versie kan snel in de template leven.
  - Zodra de logica groeit, is opsplitsen naar aparte CSS- en JS-bestanden onderhoudbaarder.
  - Dat is een praktische evolutie: eerst werkend, daarna netjes geordend.

- [data-model] gedeelde querylaag met verse per-request querysets
  - Annotaties voorkomen N+1-queries en maken choice counts goedkoop beschikbaar.
  - `Choice.votes` blijft als compatibele cache bestaan, zodat de bestaande HTML-pagina's niet direct hoeven mee te veranderen.
  - `user_choice_id` laat de frontend zien welke keuze de huidige gebruiker al heeft gemaakt.
  - Een gedeelde `QuestionQuerySet` voorkomt duplicatie tussen HTML- en API-laag.
  - Verse querysets per request zorgen ervoor dat de UI altijd actuele data toont, zeker na create, update of delete (hier 'choices').

- [choice-deletion] veilige nested lookup
  - De delete-actie moet altijd gebonden blijven aan de juiste vraag.
  - `get_object_or_404(..., question=question)` voorkomt dat een choice van een andere vraag per ongeluk wordt verwijderd.
  - De browserconfirmatie biedt een simpele extra veiligheidslaag zonder backendcomplexiteit.

### Testen

- In de codebase bestaat een werkende frontend-doorloop met expliciete testnamen zoals:
  - `test_api.py::PollsApiTests::test_api_frontend_page_sets_csrf_cookie_and_loads_alpine`
  - `test_api.py::PollsApiTests::test_api_add_choice_creates_choice_for_question`
  - `test_api.py::PollsApiTests::test_api_update_choice_changes_choice_text`
  - `test_api.py::PollsApiTests::test_api_delete_choice_removes_choice_for_question`
- De API-voteflow is afgedekt met tests zoals:
  - `test_api.py::PollsApiVoteTests::test_api_vote_creates_user_vote_and_returns_updated_detail`
  - `test_api.py::PollsApiVoteTests::test_api_vote_rejects_duplicate_vote`
- De nieuwste state-logica wordt beschermd door:
  - `test_api.py::PollsApiTests::test_api_question_detail_includes_user_choice_id_for_authenticated_user`

### Waarom we `QuestionManager` gebruiken

In de API gebruiken we een custom manager op `Question` om querylogica te centraliseren. `QuestionManager` levert een `QuestionQuerySet` met extra methoden:

- `with_choice_count()` voegt met `annotate(choice_count=Count("choice"))` een keuze-telling toe aan elke vraag, zodat we op de lijstpagina geen extra count-queries per vraag hoeven uit te voeren.
- `with_choices()` gebruikt `prefetch_related("choice_set")` zodat de keuze-rijen voor een vraag één keer worden opgehaald, wat een N+1-probleem voorkomt in de detailweergave.

Door deze logica in de manager te zetten, blijft zowel `api_views.py` als `views.py` overzichtelijk. In plaats van overal dezelfde annotatie- en prefetch-regels opnieuw te schrijven — zoals in de `IndexView` die ook `with_choice_count()` nodig heeft — roepen we gewoon:

```python
queryset = cast(QuestionManager, Question.objects).with_choice_count().order_by("-pub_date")
```

Dat betekent dat de viewset en de gewone Django `ListView` beide een `QuestionManager` gebruiken die altijd een `QuestionQuerySet` teruggeeft met de extra helper-methoden. Daarmee wordt het correct samenstellen van de query een herbruikbare service in plaats van een losse view-detailregel.

### Performance

- Phase 7 is een performancegerichte frontendfase: we willen een snelle API-gedreven pagina zonder onnodige browser- of netwerkbelasting.
- De backend beperkt de poll vragenlijst op de API kant tot de laatste 20 vragen met een echte query-limiet. Dat betekent dat het niet eerst alle vragen uit de database haalt en daarna in Python afsnoeit, maar dat alleen de benodigde 20 records via SQL worden geladen. Voor nu geen paginatie, het huidige systeem is genoeg ter demonstratie, paginatie komt terug in fase 8.
- De frontend gebruikt Alpine.js zonder buildstap en beperkt fetches tot wat echt nodig is: de geselecteerde vraag, de bijbehorende choices en de actuele user-choice state.
- CRUD-acties blijven lichtgewicht door alleen de relevante question/detail state te verversen en geen volledige applicatie-herlaad uit te voeren.
- De backend-CRUD endpoints moeten ook efficiënt zijn: gedeelde querylogica voorkomt N+1-situaties bij choice lists, vote-status en user_choice_id.
- Dit betekent dat de performance in fase 7 zowel in de browser als op het serverniveau wordt gewaarborgd: snelle reacties, beperkte DOM-updates en een API die alleen de benodigde payloads levert.

### Problemen en oplossingen

- De eerste versie had inline CSS en JavaScript, wat de onderhoudbaarheid op de langere termijn bemoeilijkte.
  - Oplossing: de frontendcode opgesplitst naar `djangotutorial/polls/static/polls/api_frontend.js` en `api_frontend.css`.
- De geselecteerde stem moest in de UI beschikbaar zijn, anders bleef de gebruiker een onjuiste vote-state zien.
  - Oplossing: `user_choice_id` toevoegen aan de question detail serializer en deze state in de frontend gebruiken om input uit te schakelen en de gekozen optie te markeren.
- Duplicate vote-logica dreigde zowel in de HTML- als de API-flow opnieuw te verschijnen.
  - Oplossing: `polls/services.py` gebruiken om `cast_vote()` te centraliseren en de backendregels in beide routes te delen.
- Na create/update/delete werd de question list soms niet vers genoeg weergegeven.
  - Oplossing: het detail opnieuw laden na writes en de lijst opnieuw ophalen zodat `choice_count` altijd up-to-date is.
- Delete moest veilig zijn en alleen de juiste question-bound choice verwijderen.
  - Oplossing: een nested delete action implementeren met `get_object_or_404(Choice, pk=choice_id, question=question)` en een browserconfirmatie voor het verwijderen.
- De eerste versie van de choice-auth was een handmatige logincheck in de methode, vooral omdat ik DRF permissions toen nog niet scherp genoeg had uitgewerkt.
  - Oplossing: de keuze omgezet naar DRF permissions en centraal gemaakt in `get_permissions()`, zodat de security niet meer door de businesslogica heen loopt.
- Een decorator per methode is op zich netjes en lokaal zichtbaar, maar bij meerdere write-actions kan de beveiliging over de methodeblokken verspreid raken.
  - Oplossing: in deze viewset de grouped variant gebruiken, zodat alle write-regels op één plek blijven en de afstand tussen de security-regel en de action klein blijft.

### Vragen

- (real) Welke aanpakken overweeg je voor een API-gedreven frontend en waarom kies je in deze versimpelde situatie voor Alpine.js via CDN?
  - Antwoord: Alpine.js via CDN is de lichtste oplossing die JSON kan renderen, loading/foutstates kan beheren en dezelfde browser zonder build tooling kan gebruiken. Het is minder riskant dan een React/Vue build en past beter bij de opdracht dan HTMX omdat de app expliciet een REST JSON-API gebruikt.
- (added) Waarom geen token- of JWT-authenticatie voor deze frontend?
  - Antwoord: de app draait op dezelfde origin als Django en gebruikt al session-based login. Session auth + CSRF is eenvoudiger en veiliger voor deze use case dan extra tokenbeheer.
- (added) Hoe zorg je dat choice create/update/delete niet leidt tot verouderde question counts in de sidebar?
  - Antwoord: na elke write wordt de geselecteerde question herladen en de lijstvragen opnieuw opgehaald, zodat `choice_count` en de gekozen optie altijd met de laatste API-state synchroniseren.
- (added) Waarom voeg je `user_choice_id` toe aan de detail payload?
  - Antwoord: dat maakt het voor de frontend mogelijk om te weten welke keuze de gebruiker al heeft gemaakt en de vote UI daarop aan te passen, zonder extra API-calls of client-only tracking.
- (added) Waarom kies je voor `get_permissions()` in plaats van een decorator per methode?
  - Antwoord: ik kies hier voor de grouped variant omdat alle write-permissions centraal op één plek blijven en daardoor makkelijker te scannen en te onderhouden zijn. Een decorator per methode blijft wel een goed alternatief als de viewset later wordt opgesplitst of je veel grotere afstand tussen acties krijgt.

-----------------------

## Phase 8: Audit Log (Wat en Wie)

### Algemene opdracht observatie

Deze fase vraagt expliciet om een historische audit trail: een overzicht van wie welke wijziging heeft doorgevoerd en wat er precies is veranderd. Rollback of herstel van oude versies is niet nodig; het gaat alleen om traceerbaarheid en transparantie van de mutaties.

### Kern onderdelen van deze opdracht

- Maak een audit-systeem dat schrijft bij mutaties in de polls-app.
- Bewaar actor (user), model, object-id, event en before/after informatie.
- Zorg dat de auditregels niet verdwijnen wanneer het doelobject later verwijderd wordt.
- Voeg een leesbare API toe voor de auditlog met paginering en filters.
- Laat de auditlog in de API-frontend terugzien zonder een nieuwe front-end stack toe te voegen.

### Opties

- [audit-opslag]
  - Gebruik een dedicated `AuditLog` model in de app.
  - Gebruik een third-party geschiedenispakket zoals `django-simple-history`.
  - Log met generieke signals en threadlocal request-context.

- [audit-relatie]
  - Koppel auditregels via foreign keys aan het doelmodel.
  - Bewaar alleen een string-`object_id` en modelnaam.
  - Bewaar beide voor maximale betrouwbaarheid.

- [audit-privacy]
  - Houd auditregels intact ook nadat een gebruiker is verwijderd.
  - Verwijder auditregels als de gekoppelde gebruiker weg is vanwege GDPR/AVG.
  - Anonimiseer alleen het gebruikersgedeelte van de auditregel bij accountverwijdering.

- [audit-schrijfpunt]
  - Schrijf auditregels in middleware/signals buiten de businesslogica.
  - Schrijf auditregels direct op de 'mutation boundaries' in de services/viewset.

- [frontend-weergave]
  - Voeg een aparte audit-tab in de bestaande Alpine.js-pagina toe.
  - Bouw een losse auditpagina of admin-interface.
  - Gebruik server-rendered HTML voor de auditlijst.

- [filter-strategieën]
  - Bied meerdere filter-types aan: gebruiker (autocomplete), model (dropdown), event (dropdown).
  - Bied alleen vrije-text filters aan.
  - Bied pre-gedefinieerde filter-combinaties aan (bijv. "mijn recent wijzigingen").

- [filter-trigger]
  - Filters triggeren direct onmiddellijke zoeking (debounce op user input, direct op select/dropdown).
  - Filters triggeren alleen na het klikken op een "Apply"-knop.
  - Filters triggeren met een vertraging voor alle inputtypen.

- [user-autocomplete]
  - Dynamische autocomplete via datalist, gevoed door een `/api/polls/audit/users/` eindpunt.
  - Statische dropdown met alle beschikbare gebruikersnamen.
  - Vrije-text zoekinvoer zonder voorgestelde opties.

- [paginering-ui]
  - Previous/Next knoppen voor pagina's.
  - Paginanummers (1, 2, 3...) voor directe navigatie.
  - "Load more" oneindig scrollen.

- [snapshot-formaat]
  - Raw JSON in code blocks (monospace).
  - Pretty-printed JSON met inspringen.
  - Alleen key-value paren of samenvatting.

### Gekozen opties

- [audit-opslag]
  - Kies voor een dedicated `AuditLog` model in de `polls`-app. (one-to-many :: 1 FK)
- [audit-relatie]
  - Kies voor een string-gebaseerde `object_id` plus modelnaam, zonder FK naar de doelmodellen.
- [audit-schrijfpunt]
  - Kies om auditregels direct te schrijven op de mutation boundaries in `cast_vote()` en in `QuestionViewSet` choice CRUD.
- [frontend-weergave]
  - Kies voor een audit-tab binnen de bestaande API-frontendpagina.
- [audit-privacy]
  - Kies om de auditregels te bewaren waar mogelijk, maar persoonlijke gebruikersgegevens bij accountverwijdering te anonymiseren of te verwijderen in lijn met GDPR/AVG.
- [filter-strategieën]
  - Kies voor drie aparte filter-types: gebruiker (autocomplete), model (dropdown), event (dropdown).
- [filter-trigger]
  - Kies voor direct triggering: gebruiker-input met debounce (250ms), select/dropdown met onmiddellijke verandering.
- [user-autocomplete]
  - Kies voor dynamische autocomplete via datalist, gevoed door `/api/polls/audit/users/`.
- [paginering-ui]
  - Kies voor Previous/Next knoppen met URL-gebaseerde paginering.
- [snapshot-formaat]
  - Kies voor raw JSON in code blocks.

### Waarom zijn deze opties gekozen

- [audit-opslag] dedicated `AuditLog`-model
  - Een eigen model houdt de audit trail expliciet en begrijpelijk.
  - `django-simple-history` zou rollback en extra modelversies toevoegen, terwijl rollback hier buiten scope valt.
  - Signals met request-context maken de flow minder zichtbaar en lastiger te debuggen.
  - Door direct te loggen in de businesslaag blijft duidelijk waar de mutatie en de audit samenkomen.

- [audit-relatie] string-based `object_id` plus modelnaam
  - De auditregel moet bruikbaar blijven, ook als het doelobject later verdwijnt.
  - Een foreign key zou de historie kwetsbaar maken zodra een vraag, keuze of stem wordt verwijderd.
  - Met een losse object-id en modelnaam blijft de log leesbaar en los van de levenscyclus van het bronobject.

- [audit-privacy] bewaren waar mogelijk, anonimiseren of verwijderen waar nodig
  - Auditgeschiedenis is waardevol, maar persoonlijke gegevens moeten wel zorgvuldig behandeld worden.
  - Als gebruikerdata later verwijderd of geanonimiseerd moet worden, blijft de afweging expliciet in beeld.
  - Zo blijft de log bruikbaar zonder te doen alsof privacy-eisen niet bestaan.

- [audit-schrijfpunt] direct op mutation boundaries
  - De mutatie en de auditregel horen dicht bij elkaar te staan.
  - Dat maakt de code testbaar, voorspelbaar en makkelijk te volgen.
  - Signals zijn hier niet nodig, omdat de app een beperkt aantal duidelijke write-punten heeft.
  - De bestaande service- en viewsetstructuur leent zich juist goed voor directe logging.

- [frontend-weergave] audit-tab in de bestaande pagina
  - Eén extra tab houdt de gebruikerservaring compact en hergebruikt de bestaande API-frontend.
  - Een losse auditpagina of nieuw framework zou meer UI-werk en meer onderhoud betekenen.
  - Binnen de huidige opzet is een tab de snelste en duidelijkste manier om auditdata zichtbaar te maken.

- [filter-strategieën] gebruiker, model en event
  - Deze filters sluiten aan op hoe je meestal naar een auditlog kijkt.
  - Vrije tekst alleen zou te vaag zijn; vaste combinaties zouden juist te star zijn.
  - Drie duidelijke filters geven een goede balans tussen eenvoud en bruikbaarheid.

- [filter-trigger] direct met debounce
  - Gebruikers willen snel resultaat zien zonder extra klik op een apply-knop.
  - Debounce op tekstinvoer beperkt onnodige requests.
  - Direct reageren op dropdownwijzigingen maakt de interface voorspelbaar en vlot.

- [user-autocomplete] datalist via `audit-users`-endpoint
  - Suggesties tijdens het typen maken zoeken vriendelijker en verminderen typfouten.
  - Een statische dropdown zou op termijn te groot en te omslachtig worden.
  - Vrije tekst zonder suggesties zou de kans op foutieve filters vergroten.

- [paginering-ui] Previous/Next met URL-gebaseerde paginering
  - Voor deze log is sequentieel bladeren voldoende.
  - Previous/Next is eenvoudiger dan paginanummers of infinite scroll.
  - URL-gebaseerde paginering blijft goed deelbaar en herkenbaar.

- [snapshot-formaat] raw JSON in code blocks
  - Raw JSON sluit het best aan op de API-responsen.
  - Het houdt de frontend compact en direct leesbaar.
  - Pretty-printing of extra samenvattingen zijn erg fraai, maar dat was niet perse de opdracht.

### Testen

- Er zijn audit-specifieke tests toegevoegd voor:
  - `test_audit.py::AuditLogApiTests::test_audit_log_list_orders_newest_first_and_paginates`  
  - `test_audit.py::AuditLogApiTests::test_audit_log_list_filters_by_model_and_event`
  - `test_audit.py::AuditLogApiTests::test_audit_log_list_filters_by_user`
- Samen zorgen deze testlagen ervoor dat de audittrail leesbaar blijft en dat alleen echte mutaties worden vastgelegd. 
  - Dit gezien er alleen een audit log ontstaat wanneer alles goed ging, dus geen errors. Nu zouden we dus ook een tweede log kunnen aanmaken voor deze errors, maar dan heb je het over een error-log.

### Performance

- De audit opslag blijft binnen de app performant door de belangrijkste zoekpaden te ondersteunen met indexen. Een index op `created_at` voor de 'newest-first' listing en aanvullende indexen op `model` en `event` maken de auditlijst snel filterbaar.
- Voor de auditlijst is paginering essentieel: de frontend vraagt nooit meer dan een enkele page met regels op, zodat zowel database- als browser-geheugen bounded blijft. Hierdoor blijft de lijst- en filterflow schaalbaar zonder extra cachinglagen.
- `select_related("user")` is belangrijk voor de audit read path, zodat actor-namen en user-filters geen N+1-querypatroon veroorzaken. Dit houdt de read-side efficiënt, zelfs bij groeiende historie.
- We vermijden in Phase 8 extra complexe cache-infrastructuur. Omdat de auditdata meteen over de API wordt gepagineerd en gefilterd, is een simpele query-gedreven aanpak met goede indexen voldoende binnen deze assessment scope.

### Problemen en oplossingen

- Het is verleidelijk om `django-simple-history` te gebruiken, omdat het een beproefde package is, maar het voegt rollback-concepten en extra afhankelijkheden toe zonder dat de opdracht daarom vraagt en dus extra complexiteit.
  - Oplossing: een eigen `AuditLog` model gebruiken met expliciete write-punten op de mutation boundaries.
- Een foreign key naar het doelobject maakt de auditregel onbruikbaar nadat het object is verwijderd.
  - Oplossing: een plain `object_id` plus modelnaam gebruiken, zodat de log leesbaar blijft ook wanneer de bron verdwijnen is.
- Bij verwijdering van een gebruiker ontstaat een spanning tussen GDPR/AVG vereisten (persoonlijke data verwijderen) en audittrail duurzaamheid (geschiedenis behouden).
  - Oplossing: architectuur implementeren zodat auditregels kunnen worden verwijderd wanneer een gebruiker weg is, maar met bewustwording dat dit een expliciete keuze is (niet anonimisering, maar verwijdering).
- Het auditmechanisme moet zichtbaar blijven in code, niet verborgen in een signal-keten.
  - Oplossing: auditregels direct schrijven op de mutation boundary in de view/service layer, zodat iemand die de code leest onmiddellijk ziet waar en hoe audit plaatsvindt.
  - Mogelijk moet dit anders worden ingericht bij meer complexe apps, gezien we anders te veel losse 'audit aanmaak calls' krijgen.
- Filterinterface kan overbelast worden met te veel inputvelden, vooral op mobiel.
  - Oplossing: drie duidelijk gescheiden filter-inputs (gebruiker, model, event), elk met een specifiek doel, zodat gebruikers snel kunnen filteren zonder overload.
- Autocomplete voor gebruikersnamen vereist een extra API-endpoint.
  - Oplossing: een eenvoudige `/api/polls/audit/users/` endpoint toevoegen die de unieke usernamen retourneert; dit wordt één keer geladen bij een pagina init.
- JSON snapshots kunnen heel lang zijn en veel schermruimte innemen.
  - Oplossing: code blocks gebruiken met monospace font, zodat JSON compact en scanbaar blijft; geen pretty-printing of expanders, omdat de data per entry klein genoeg is. (dit kan verandering na scope verandering, maar niet in het in huidige project)

### Vragen

- (real) Welke aanpakken overweeg je voor een audit log en waarom kies je in deze situatie voor een dedicated model met directe schrijfpunten?
  - Antwoord: ik overweeg `django-simple-history`, generieke signals met request-context en een eigen auditmodel. Ik kies voor het eigen auditmodel omdat het de exacte businessvraag oplost zonder extra rollback- of dependency-complexiteit, en omdat de schrijfpunten in deze app klein en duidelijk zijn.
- (added) Waarom gebruik je geen foreign key naar het doelmodel in de auditregel?
  - Antwoord: een foreign key wordt ongeldig als het doelobject wordt verwijderd. Voor auditdoeleinden is het belangrijk dat de historie bruikbaar blijft, ook nadat de originele record weg is.
- (added) Hoe ga je om met GDPR/AVG vereisten wanneer een gebruiker zijn account verwijdert?
  - Antwoord: de huidige implementatie verwijdert auditregels via cascade-delete wanneer de gebruiker weg is. Dit is een expliciete keuze met voor- en nadelen: persoonlijke data wordt volledig verwijderd (GDPR-compliant), maar de volledige audittrail gaat verloren. Toekomstige updates zouden kunnen overwegen om auditregels te anonimiseren in plaats van te verwijderen, zodat de geschiedenis bruikbaar blijft voor compliance-doeleinden.
- (added) Waarom kies je voor een audit-tab in de bestaande frontend in plaats van een losse auditpagina?
  - Antwoord: die keuze hergebruikt de bestaande API-frontend en de session/CSRF-logica, waardoor de scope klein blijft en implementatie eenvoudig blijft.
- (added) Hoe zorg je dat een mislukte of dubbele mutatie geen auditregel achterlaat?
  - Antwoord: auditregels worden pas geschreven na een succesvolle mutatie, en alleen op de mutation boundary. Bij een duplicate vote of mislukte choice-validatie komt er geen auditrecord, omdat de auditregel-schrijf pas na de succesvol gemaakte write gebeurt.
- (added) Waarom kies je voor direct schrijven van auditregels in plaats van Django signals?
  - Antwoord: signals verbergen de audit-logica achter onzichtbare handlers, wat in een kleine app met slechts 3-4 mutation points onnodig complexiteit toevoegt. Direct schrijven in `cast_vote()` en viewset actions houdt de flow lineair en testbaar. Signals worden pas nuttig in grotere apps met meerdere triggerpunten of cross-app afhankelijkheden, wat hier niet het geval is.

> BELANGRIJK :: De volgende fase heb ik niet daadwerkelijk behandeld, gezien tijdsredenen.
> Hieronder belicht ik nog wel wat ik conceptueel zou willen doen.

## Phase 9: Eigenaarschap & Object-Level Permissions (ACL)

**Doel:** Implementeren van eigenaarschap op `Question` zodat alleen de eigenaar mag wijzigen (`PUT/PATCH/DELETE`), terwijl de rest van de wereld mag stemmen (`POST` op gerelateerde Choice).

- **Gekozen aanpak:** Een `owner` ForeignKey op `Question`. In DRF gebruiken we een custom permission class `IsOwnerOrReadOnly`.
- **Bespreekpunt: Ontwerp & Relevante Aspecten:**
  - **IDOR-preventie:** Door op object-niveau te controleren (`obj.owner == request.user`), voorkomen we *Insecure Direct Object Reference*. Zonder dit zou een kwaadwillende gebruiker simpelweg een `question_id` in een URL kunnen gokken en andermans data wijzigen.
  - **Granulariteit:** Het ontwerp scheidt "beheer" (Question) van "interactie" (Vote). Een relevante afweging is dat permissies op de `Question` viewset niet automatisch stemmen blokkeren op de `Choice` viewset. Dit is een bewuste keuze voor een soepele API-ervaring.
  - **Horizontale Privilege Escalatie:** We voorkomen dat gebruikers met dezelfde 'rol' elkaars data aanpassen. Een simpele ForeignKey-check is de meest robuuste basis voordat je naar complexe oplossingen als `django-guardian` grijpt.

> BELANGRIJK :: De volgende fase heb ik niet daadwerkelijk behandeld, gezien tijdsredenen.
> Hieronder belicht ik nog wel wat ik conceptueel zou willen doen.

## Phase 10: Dashboard & Bulk Data Generatie

**Doel:** Een analytics-overzicht van top-stemmers en een efficiënt script om dit te testen met significante datasets.

- **Gekozen aanpak:** Database-aggregatie via `Count` en een Django Management Command met `bulk_create`.
- **Bespreekpunt: Efficiëntie, Schaalbaarheid & Voorbereiding:**
  - **Database vs. Python:** Het dashboard berekent de stemmen in de database via SQL (`GROUP BY`). Dit is vele malen sneller dan tienduizenden Vote-objecten in Python-geheugen laden en tellen.
  - **Indexering:** Om dit schaalbaar te houden, bereid ik de database voor door een index te plaatsen op de `user_id` in de `Vote`-tabel. Dit zorgt ervoor dat de `Count` operatie ook bij miljoenen rijen razendsnel blijft.
  - **Bulk Operations:** Het script gebruikt `bulk_create` om data in batches van bijv. 1000 rijen te schrijven. Dit minimaliseert het aantal database-transacties en voorkomt netwerk-overhead, wat essentieel is bij het genereren van realistische testsets.
  - **Caching:** Als voorbereiding op extreme groei zouden we *Materialized Views* of *Caching (Redis)* kunnen gebruiken, dit om de top-voters niet bij elke page-refresh opnieuw te hoeven berekenen.
