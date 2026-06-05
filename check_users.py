#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Проверка всех пользователей в БД
"""

from db.database import get_session
from db.repositories import UserRepository
from services.services import ExchangeRateService

print("=== ПРОВЕРКА ВСЕХ ПОЛЬЗОВАТЕЛЕЙ В БД ===\n")

session = get_session()
user_repo = UserRepository(session)
users = user_repo.get_all_users()

print(f"Всего пользователей в БД: {len(users)}\n")

for i, user in enumerate(users, 1):
    print(f"{i}. Username: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   ID: {user.id}")
    
    # Получить курсы этого пользователя
    rates = ExchangeRateService.get_user_rates(user.id)
    print(f"   Курсы: {len(rates)} шт")
    for (from_c, to_c), rate in sorted(rates.items())[:3]:
        print(f"      - {from_c} -> {to_c}: {rate:.4f}")
    print()

session.close()
