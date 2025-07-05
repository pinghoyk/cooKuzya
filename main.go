package main

import (
	"encoding/json"
	"log"
	"os"
	"strings"
	"time"

	"github.com/joho/godotenv"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

// Структуры для локализации
type Locale struct {
	Bot     BotLocale     `json:"bot"`
	Buttons ButtonsLocale `json:"buttons"`
	Commands CommandsLocale `json:"commands"`
}

type BotLocale struct {
	Welcome string      `json:"welcome"`
	Help    string      `json:"help"`
	Save    SaveMessages `json:"save"`
}

type SaveMessages struct {
	None string `json:"none"`
	Yes  string `json:"yes"`
}

type ButtonsLocale struct {
	Back     string `json:"back"`
	Favorites string `json:"favorites"`
	Delete   string `json:"delete"`
	Read     string `json:"read"`
}

type CommandsLocale struct {
	Start string `json:"start"`
	Help  string `json:"help"`
}

// Загружает локализацию из файла
func loadLocale(path string) (*Locale, error) {
	file, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var locale Locale
	err = json.Unmarshal(file, &locale)
	return &locale, err
}

// Заменяет плейсхолдеры в строке значениями из map
func formatMessage(template string, params map[string]string) string {
	result := template
	for key, value := range params {
		placeholder := "{" + key + "}"
		result = strings.ReplaceAll(result, placeholder, value)
	}
	return result
}

func main() {
	locale, err := loadLocale("locales.json")  // Загрузка локализации
	if err != nil {
		log.Fatalf("Ошибка загрузки локализации: %v", err)
	}

	err = godotenv.Load()  // Загрузка переменных их .env
	if err != nil {
		log.Fatalf("Ошибка загрузки .env: %v", err)
	}

	token := os.Getenv("BOT_TOKEN")
	if token == "" {
		log.Fatal("BOT_TOKEN не установлен в .env")
	}

	bot, err := tgbotapi.NewBotAPI(token)
	if err != nil {
		log.Panicf("Ошибка инициализации бота: %v", err)
	}

	bot.Debug = true
	log.Printf("Бот %s запущен", bot.Self.UserName)

	// Настройка команд бота
	commands := []tgbotapi.BotCommand{
		{Command: "start", Description: locale.Commands.Start},
		{Command: "help", Description: locale.Commands.Help},
	}
	_, err = bot.Request(tgbotapi.NewSetMyCommands(commands...))
	if err != nil {
		log.Printf("Ошибка установки команд: %v", err)
	}

	u := tgbotapi.NewUpdate(0)
	u.Timeout = 30
	updates := bot.GetUpdatesChan(u)

	for update := range updates {
		if update.Message == nil {
			continue
		}

		log.Printf(
			"[%s][%d] %s",
			time.Now().Format(time.DateTime),
			update.Message.From.ID,
			update.Message.Text,
		)

		if update.Message.IsCommand() {
