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
