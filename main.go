package main

import (
	"encoding/json"
	"log"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/joho/godotenv"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

// Структуры для локализации
type Locale struct {
	Bot      BotLocale      `json:"bot"`
	Buttons  ButtonsLocale  `json:"buttons"`
	Commands CommandsLocale `json:"commands"`
}

type BotLocale struct {
	Welcome string       `json:"welcome"`
	Help    string       `json:"help"`
	Save    SaveMessages `json:"save"`
}

type SaveMessages struct {
	None string `json:"none"`
	Yes  string `json:"yes"`
}

type ButtonsLocale struct {
	Back      string `json:"back"`
	Favorites string `json:"favorites"`
	Delete    string `json:"delete"`
	Read      string `json:"read"`
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

// Заменяет названия типа {name} значениями из map
func formatMessage(template string, params map[string]string) string {
	result := template
	for key, value := range params {
		placeholder := "{" + key + "}"
		result = strings.ReplaceAll(result, placeholder, value)
	}
	return result
}


func main() {
	locale, err := loadLocale("locales.json") // берет файл локализации
	if err != nil {
		log.Fatalf("Ошибка загрузки локализации: %v", err)
	}

	err = godotenv.Load() // берет файл .env
	if err != nil {
		log.Fatalf("Ошибка загрузки файла .env: %v", err)
	}

	token := os.Getenv("BOT_TOKEN")
	if token == "" {
		log.Fatal("Токена не существует в .env")
	}

	bot, err := tgbotapi.NewBotAPI(token) // запускаем бота
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
		log.Printf("Ошибка установки команд %v", err)
	}


	// Храним ID последнего активного меню
		var menuMessages = make(map[int64]int)
		var menuMutex sync.Mutex

		// Функция для удаления предыдущего меню
		deletePreviousMenu := func(chatID int64) {
			menuMutex.Lock()
			defer menuMutex.Unlock()

			if msgID, exists := menuMessages[chatID]; exists {
				deleteMsg := tgbotapi.NewDeleteMessage(chatID, msgID)
				if _, err := bot.Request(deleteMsg); err != nil {
					log.Printf("Ошибка удаления меню: %v", err)
				}
				delete(menuMessages, chatID)
			}
		}

		// Функция отправки стартового меню
		sendStartMenu := func(chatID int64, firstName string) {
			deletePreviousMenu(chatID)

			messageText := formatMessage(locale.Bot.Welcome, map[string]string{
				"name": firstName,
			})

			msg := tgbotapi.NewMessage(chatID, messageText)
			msg.ReplyMarkup = tgbotapi.NewInlineKeyboardMarkup(
				tgbotapi.NewInlineKeyboardRow(
					tgbotapi.NewInlineKeyboardButtonData(locale.Buttons.Favorites, "favorites"),
				),
			)

			sentMsg, err := bot.Send(msg)
			if err != nil {
				log.Printf("Ошибка отправки меню: %v", err)
				return
			}

			menuMutex.Lock()
			menuMessages[chatID] = sentMsg.MessageID
			menuMutex.Unlock()
		}

		// Функция отправки меню помощи
		sendHelpMenu := func(chatID int64) {
			deletePreviousMenu(chatID)

			msg := tgbotapi.NewMessage(chatID, locale.Bot.Help)
			msg.ReplyMarkup = tgbotapi.NewInlineKeyboardMarkup(
				tgbotapi.NewInlineKeyboardRow(
					tgbotapi.NewInlineKeyboardButtonData(locale.Buttons.Back, "back"),
				),
			)

			sentMsg, err := bot.Send(msg)
			if err != nil {
				log.Printf("Ошибка отправки меню помощи: %v", err)
				return
			}

			menuMutex.Lock()
			menuMessages[chatID] = sentMsg.MessageID
			menuMutex.Unlock()
		}

		// Функция отправки избранного
		sendFavoritesMenu := func(chatID int64) {
			deletePreviousMenu(chatID)

			msg := tgbotapi.NewMessage(chatID, locale.Bot.Save.None)
			msg.ReplyMarkup = tgbotapi.NewInlineKeyboardMarkup(
				tgbotapi.NewInlineKeyboardRow(
					tgbotapi.NewInlineKeyboardButtonData(locale.Buttons.Back, "back"),
				),
			)

			sentMsg, err := bot.Send(msg)
			if err != nil {
				log.Printf("Ошибка отправки избранного: %v", err)
				return
			}

			menuMutex.Lock()
			menuMessages[chatID] = sentMsg.MessageID
			menuMutex.Unlock()
		}

		u := tgbotapi.NewUpdate(0)
		u.Timeout = 30
		updates := bot.GetUpdatesChan(u)

		for update := range updates {
			// Обработка нажатий на кнопки
			if update.CallbackQuery != nil {
				chatID := update.CallbackQuery.Message.Chat.ID

				switch update.CallbackQuery.Data {
				case "favorites":
					sendFavoritesMenu(chatID)

				case "back":
					sendStartMenu(chatID, update.CallbackQuery.From.FirstName)
				}

				// Подтверждаем обработку callback
				callback := tgbotapi.NewCallback(update.CallbackQuery.ID, "")
				if _, err := bot.Request(callback); err != nil {
					log.Printf("Ошибка callback: %v", err)
				}
				continue
			}

			if update.Message == nil {
				continue
			}

			log.Printf(
				"[%s][%d] %s",
				time.Now().Format(time.DateTime),
				update.Message.From.ID,
				update.Message.Text,
			)

			// Удаляем сообщение пользователя сразу после получения
			deleteMsg := tgbotapi.NewDeleteMessage(update.Message.Chat.ID, update.Message.MessageID)
			if _, err := bot.Request(deleteMsg); err != nil {
				log.Printf("Ошибка удаления сообщения: %v", err)
			}

			if update.Message.IsCommand() {
				switch update.Message.Command() {
				case "start":
					sendStartMenu(update.Message.Chat.ID, update.Message.From.FirstName)
				case "help":
					sendHelpMenu(update.Message.Chat.ID)
				}
			} else {
				// Для любого текста показываем стартовое меню
				sendStartMenu(update.Message.Chat.ID, update.Message.From.FirstName)
			}
		}