# Project Board (GitHub Projects v2): настройка
1. Создать проект (вариант CLI):
   ```bash
   OWNER_OR_ORG=<your_login_or_org>
   PROJECT_TITLE="SMDaI Board"
   gh auth status
   ./scripts/setup_project.sh
   ```
   Скрипт напечатает URL проекта.
   Опционально: привяжите репозиторий к проекту, чтобы он отображался во вкладке Projects репозитория:
   ```bash
   GH_TOKEN=$SMD_PROJECT_PAT gh project link <NUMBER> --owner $OWNER_OR_ORG --repo <OWNER/REPO>
   ```
2. Добавить секрет в репозиторий:
   Settings → Secrets → Actions → New repository secret
   Name: PROJECT_URL, Value: <вставьте URL из шага 1>.
   Дополнительно: создайте PAT со скоупами repo, project и добавьте его как секрет `SMD_Project_Repo` — он используется в workflow triage для доступа к Projects v2.
3. Проверка:

* Откройте новый Issue — он должен появиться в проекте (см. также ссылку на проект во вкладке Projects репозитория).
* Новый PR также попадёт в проект (если включён triage-pr.yml).
