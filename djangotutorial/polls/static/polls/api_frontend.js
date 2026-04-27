window.pollsFrontend = function pollsFrontend() {
  return {
    apiBaseUrl: "",
    auditBaseUrl: "",
    isAuthenticated: false,
    activeTab: "polls",
    loadingQuestions: false,
    questions: [],
    selectedQuestion: null,
    selectedChoiceId: null,
    newChoiceText: "",
    editingChoiceId: null,
    editingChoiceText: "",
    ignoreChoiceBlurSave: false,
    choiceBlurTimer: null,
    view: "index",
    errorMessage: "",
    loadError: "",
    auditLoading: false,
    auditEntries: [],
    auditNextUrl: null,
    auditPreviousUrl: null,
    auditError: "",
    auditCount: 0,
    auditUserOptions: [],
    auditUserFilter: "",
    auditModelFilter: "",
    auditEventFilter: "",
    hasLoadedQuestions: false,

    async init() {
      if (this.hasLoadedQuestions) {
        return;
      }

      const {
        apiBaseUrl = "",
        auditBaseUrl = "",
        isAuthenticated = "false",
      } = this.$el.dataset;
      this.apiBaseUrl = apiBaseUrl;
      this.auditBaseUrl = auditBaseUrl;
      this.isAuthenticated = isAuthenticated === "true";
      this.hasLoadedQuestions = true;
      await this.loadQuestions();
      await this.loadAuditUsers();
    },

    getCsrfToken() {
      const cookie = document.cookie
        .split("; ")
        .find((row) => row.startsWith("csrftoken="));

      return cookie ? decodeURIComponent(cookie.split("=")[1]) : "";
    },

    getApiErrorMessage(payload, fallbackMessage) {
      return (
        payload?.error_message ||
        payload?.choice_text?.[0] ||
        payload?.detail ||
        fallbackMessage
      );
    },

    setSelectedChoiceFromPayload(question) {
      this.selectedChoiceId = question?.user_choice_id ?? null;
    },

    async refreshSelectedQuestion() {
      if (!this.selectedQuestion) {
        return;
      }

      const response = await fetch(`${this.apiBaseUrl}${this.selectedQuestion.id}/`, {
        headers: {
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Could not refresh this poll.");
      }

      this.selectedQuestion = await response.json();
      this.setSelectedChoiceFromPayload(this.selectedQuestion);
      this.syncQuestionCount(this.selectedQuestion);
    },

    syncQuestionCount(updatedQuestion) {
      if (!updatedQuestion) {
        return;
      }

      const cacheEntry = this.questions.find(
        (question) => question.id === updatedQuestion.id,
      );

      if (cacheEntry) {
        cacheEntry.choice_count = updatedQuestion.choice_count;
      }
    },

    switchTab(tabName) {
      this.activeTab = tabName;

      if (tabName === "polls") {
        return;
      }

      this.loadAuditLogs();
    },

    buildAuditUrl(pageUrl = "") {
      if (pageUrl) {
        return pageUrl;
      }

      const url = new URL(this.auditBaseUrl, window.location.origin);

      if (this.auditUserFilter) {
        url.searchParams.set("user", this.auditUserFilter.trim());
      }

      if (this.auditModelFilter) {
        url.searchParams.set("model", this.auditModelFilter);
      }

      if (this.auditEventFilter) {
        url.searchParams.set("event", this.auditEventFilter);
      }

      return url.toString();
    },

    resetAuditFilters() {
      this.auditUserFilter = "";
      this.auditModelFilter = "";
      this.auditEventFilter = "";
      this.loadAuditLogs();
    },

    async loadAuditUsers() {
      try {
        const response = await fetch(`${this.auditBaseUrl}users/`, {
          headers: {
            Accept: "application/json",
          },
        });

        if (!response.ok) {
          throw new Error("Could not load audit users.");
        }

        this.auditUserOptions = await response.json();
      } catch (error) {
        // fail silently; the filter can still be typed manually
        this.auditUserOptions = [];
      }
    },

    setAuditUserFilter(username) {
      this.auditUserFilter = username;
      this.loadAuditLogs();
    },

    async loadAuditLogs(pageUrl = "") {
      this.auditLoading = true;
      this.auditError = "";

      try {
        const response = await fetch(this.buildAuditUrl(pageUrl), {
          headers: {
            Accept: "application/json",
          },
        });

        if (!response.ok) {
          throw new Error("Could not load audit log.");
        }

        const payload = await response.json();
        this.auditEntries = payload.results ?? [];
        this.auditNextUrl = payload.next;
        this.auditPreviousUrl = payload.previous;
        this.auditCount = payload.count ?? 0;
      } catch (error) {
        this.auditError = error.message || "Could not load audit log.";
      } finally {
        this.auditLoading = false;
      }
    },

    async nextAuditPage() {
      if (!this.auditNextUrl) {
        return;
      }

      await this.loadAuditLogs(this.auditNextUrl);
    },

    async previousAuditPage() {
      if (!this.auditPreviousUrl) {
        return;
      }

      await this.loadAuditLogs(this.auditPreviousUrl);
    },

    startEditChoice(choice) {
      this.editingChoiceId = choice.id;
      this.editingChoiceText = choice.choice_text;
    },

    cancelEditChoice() {
      this.editingChoiceId = null;
      this.editingChoiceText = "";
    },

    preventChoiceBlurSave() {
      this.ignoreChoiceBlurSave = true;
    },

    handleChoiceFocusOut(choiceId) {
      clearTimeout(this.choiceBlurTimer);
      this.choiceBlurTimer = setTimeout(() => {
        if (this.ignoreChoiceBlurSave) {
          this.ignoreChoiceBlurSave = false;
          return;
        }

        if (this.editingChoiceId === choiceId) {
          this.saveChoice(choiceId);
        }
      }, 120);
    },

    async loadQuestions() {
      this.loadingQuestions = true;
      this.loadError = "";

      try {
        const response = await fetch(this.apiBaseUrl, {
          headers: {
            Accept: "application/json",
          },
        });

        if (!response.ok) {
          throw new Error("Could not load polls.");
        }

        this.questions = await response.json();
      } catch (error) {
        this.loadError = error.message;
      } finally {
        this.loadingQuestions = false;
      }
    },

    async openQuestion(questionId) {
      this.errorMessage = "";
      this.selectedChoiceId = null;
      this.activeTab = "polls";
      this.view = "detail";

      try {
        const response = await fetch(`${this.apiBaseUrl}${questionId}/`, {
          headers: {
            Accept: "application/json",
          },
        });

        if (!response.ok) {
          throw new Error("Could not load this poll.");
        }

        this.selectedQuestion = await response.json();
        this.setSelectedChoiceFromPayload(this.selectedQuestion);
        this.newChoiceText = "";
        this.cancelEditChoice();
      } catch (error) {
        this.errorMessage = error.message;
      }
    },

    async vote() {
      if (!this.selectedChoiceId) {
        this.errorMessage = "You didn't select a choice.";
        return;
      }

      this.errorMessage = "";

      try {
        const response = await fetch(
          `${this.apiBaseUrl}${this.selectedQuestion.id}/vote/`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Accept: "application/json",
              "X-CSRFToken": this.getCsrfToken(),
            },
            body: JSON.stringify({
              choice: this.selectedChoiceId,
            }),
          },
        );

        const payload = await response.json();

        if (!response.ok) {
          this.errorMessage = this.getApiErrorMessage(
            payload,
            "Could not submit your vote.",
          );
          return;
        }

        this.selectedQuestion = payload;
        this.view = "results";
        this.selectedChoiceId = null;
      } catch (error) {
        this.errorMessage = "Could not submit your vote.";
      }
    },

    async createChoice() {
      if (!this.newChoiceText.trim()) {
        this.errorMessage = "Choice text is required.";
        return;
      }

      this.errorMessage = "";

      try {
        const response = await fetch(
          `${this.apiBaseUrl}${this.selectedQuestion.id}/choices/`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Accept: "application/json",
              "X-CSRFToken": this.getCsrfToken(),
            },
            body: JSON.stringify({
              choice_text: this.newChoiceText.trim(),
            }),
          },
        );

        const payload = await response.json();

        if (!response.ok) {
          this.errorMessage = this.getApiErrorMessage(
            payload,
            "Could not add this choice.",
          );
          return;
        }

        this.newChoiceText = "";
        this.selectedChoiceId = null;
        await this.refreshSelectedQuestion();
        await this.loadQuestions();
      } catch (error) {
        this.errorMessage = "Could not add this choice.";
      }
    },

    async saveChoice(choiceId) {
      if (!this.editingChoiceText.trim()) {
        this.errorMessage = "Choice text is required.";
        return;
      }

      this.errorMessage = "";

      try {
        const response = await fetch(
          `${this.apiBaseUrl}${this.selectedQuestion.id}/choices/${choiceId}/`,
          {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
              Accept: "application/json",
              "X-CSRFToken": this.getCsrfToken(),
            },
            body: JSON.stringify({
              choice_text: this.editingChoiceText.trim(),
            }),
          },
        );

        const payload = await response.json();

        if (!response.ok) {
          this.errorMessage = this.getApiErrorMessage(
            payload,
            "Could not update this choice.",
          );
          return;
        }

        this.cancelEditChoice();
        await this.refreshSelectedQuestion();
        await this.loadQuestions();
      } catch (error) {
        this.errorMessage = "Could not update this choice.";
      }
    },

    async deleteChoice(choice) {
      if (!confirm(`Delete choice "${choice.choice_text}"? This cannot be undone.`)) {
        return;
      }

      this.errorMessage = "";

      try {
        const response = await fetch(
          `${this.apiBaseUrl}${this.selectedQuestion.id}/choices/${choice.id}/`,
          {
            method: "DELETE",
            headers: {
              Accept: "application/json",
              "X-CSRFToken": this.getCsrfToken(),
            },
          },
        );

        if (!response.ok) {
          throw new Error("Could not delete this choice.");
        }

        this.cancelEditChoice();
        await this.refreshSelectedQuestion();
        await this.loadQuestions();
      } catch (error) {
        this.errorMessage = error.message || "Could not delete this choice.";
      }
    },

    backToIndex() {
      this.view = "index";
      this.selectedQuestion = null;
      this.selectedChoiceId = null;
      this.newChoiceText = "";
      this.cancelEditChoice();
      this.errorMessage = "";
    },

    backToChoices() {
      this.view = "detail";
      this.errorMessage = "";
      this.selectedChoiceId = this.selectedQuestion?.user_choice_id ?? null;
    },

    viewResults() {
      if (!this.selectedQuestion) {
        this.errorMessage = "No poll selected.";
        return;
      }

      this.view = "results";
      this.errorMessage = "";
    },
  };
};