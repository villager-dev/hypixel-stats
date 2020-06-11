import aiopypixel
import arrow
import asyncio
import discord
from discord.ext import commands
from math import floor, ceil


class Player(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.cache = self.bot.get_cog("Cache")

    @commands.group(name="player", aliases=["profile", "pp"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def player(self, ctx, player):
        await ctx.trigger_typing()

        embed = discord.Embed(color=self.bot.cc)

        p = await self.cache.get_player(player)

        online = f"{self.bot.EMOJIS['offline_status']} offline"
        last_online = arrow.Arrow.fromtimestamp(p.LAST_LOGIN / 1000).humanize()  # I love arrow
        if p.LAST_LOGIN > p.LAST_LOGOUT:
            online = f"{self.bot.EMOJIS['online_status']} online"
            last_online = "now"  # bc this value is obtained from last_login

        player_pfp = await self.cache.get_player_head(p.UUID)

        player_guild = p.GUILD
        if player_guild is None:
            player_guild = "none"
        else:
            player_guild = await self.cache.get_guild_name_from_id(p.GUILD)

        embed.set_author(name=f"{discord.utils.escape_markdown(p.DISPLAY_NAME)}'s Profile", icon_url=player_pfp)
        embed.add_field(name="Status", value=online)
        embed.add_field(name="\uFEFF", value=f"\uFEFF")
        embed.add_field(name="Last Online", value=f"{last_online}")
        embed.add_field(name="XP", value=f"{p.EXP}", inline=True)
        embed.add_field(name="\uFEFF", value=f"\uFEFF")
        embed.add_field(name="Level", value=f"{await self.cache.hypixel.calcPlayerLevel(p.EXP)}", inline=True)
        embed.add_field(name="Achievements", value=f"{len(p.ONE_TIME_ACHIEVEMENTS)}", inline=False)
        embed.add_field(name="Guild", value=f"{player_guild}", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="playerstats", aliases=["pstats", "ps", "player_stats"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def player_stats(self, ctx, player):
        await ctx.trigger_typing()

        p = await self.cache.get_player(player)

        await ctx.send(embed=discord.Embed(color=self.bot.cc, description=f"Available stats for this player (send which one you want): ``{', '.join(list(p.STATS))}``"))

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            stat = await self.bot.wait_for("message", check=check, timeout=20)
            stat = stat.content.lower()
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(color=self.bot.cc, description=self.bot.TIMEOUT_MESSAGE))
            return

        if stat not in [s.lower() for s in list(p.STATS)]:
            await ctx.send(f"{discord.utils.escape_markdown(p.DISPLAY_NAME)} doesn't have stats for that game!")
            return

        embed = discord.Embed(color=self.bot.cc)

        if stat == "arcade":
            embed.set_author(name=f"{discord.utils.escape_markdown(p.DISPLAY_NAME)}'s Arcade Stats",
                             icon_url=await self.cache.get_player_head(p.UUID))

            arcade = p.STATS["Arcade"]

            embed.add_field(name="All Time Coins", value=floor(arcade.get("coins")), inline=False)
            embed.add_field(name="Coins This Month",
                            value=arcade.get("monthly_coins_a") + arcade.get("monthly_coins_b"),
                            inline=False)
            embed.add_field(name="Coins This Week", value=arcade.get("weekly_coins_a") + arcade.get("weekly_coins_b"),
                            inline=False)
            await ctx.send(embed=embed)
        elif stat == "arena":
            embed.set_author(name=f"{discord.utils.escape_markdown(p.DISPLAY_NAME)}'s Arena Stats",
                             icon_url=await self.cache.get_player_head(p.UUID))

            arena = p.STATS["Arena"]

            embed.add_field(name="Coins", value=arena.get("coins"), inline=True)
            embed.add_field(name="\uFEFF", value=f"\uFEFF")
            embed.add_field(name="Coins Spent", value=arena.get("coins_spent"), inline=True)

            kills = sum({k: v for k, v in arena.items() if "kills_" in k}.values())
            deaths = sum({k: v for k, v in arena.items() if "deaths_" in k}.values())
            embed.add_field(name="Kills", value=kills if kills is not None else 0)
            embed.add_field(name="Deaths", value=deaths if deaths is not None else 0)
            embed.add_field(name="KDR", value=round(
                (kills if kills is not None else 0 + .00001) / (deaths if deaths is not None else 0 + .00001), 2),
                            inline=True)

            games = sum({k: v for k, v in arena.items() if "games_" in k}.values())
            wins = arena.get("wins")
            losses = sum({k: v for k, v in arena.items() if "losses_" in k}.values())
            embed.add_field(name="Games", value=games, inline=True)
            embed.add_field(name="Wins", value=wins if wins is not None else 0, inline=True)
            embed.add_field(name="Losses", value=losses, inline=True)

            total_dmg = sum({k: v for k, v in arena.items() if "games_" in k}.values())
            embed.add_field(name="Total Damage", value=total_dmg, inline=False)
            embed.add_field(name="Rating", value=round(arena.get("rating"), 2), inline=False)
            await ctx.send(embed=embed)
        elif stat == "battleground":
            embed.set_author(name=f"{discord.utils.escape_markdown(p.DISPLAY_NAME)}'s Battleground Stats",
                             icon_url=await self.cache.get_player_head(p.UUID))

            battle = p.STATS["Battleground"]

            embed.add_field(name="Coins", value=battle.get("coins"), inline=True)
            embed.add_field(name="Wins", value=battle.get("wins"), inline=True)
            embed.add_field(name="Losses", value=battle.get("losses"), inline=True)

            kills = battle.get("kills")
            deaths = battle.get("deaths")
            embed.add_field(name="Kills", value=kills if kills is not None else 0, inline=True)
            embed.add_field(name="Deaths", value=deaths if deaths is not None else 0, inline=True)
            embed.add_field(name="KDR", value=round(
                (kills if kills is not None else 0 + .00001) / (deaths if deaths is not None else 0 + .00001), 2),
                            inline=True)

            embed.add_field(name="Damage Inflicted", value=battle.get("damage"))
            embed.add_field(name="Damage Taken", value=battle.get("damage_taken"))
            embed.add_field(name="Life Leeched", value=battle.get("life_leeched"))
            await ctx.send(embed=embed)
        elif stat == "hungergames":
            embed.set_author(name=f"{discord.utils.escape_markdown(p.DISPLAY_NAME)}'s Hungergames Stats",
                             icon_url=await self.cache.get_player_head(p.UUID))

            hunger = p.STATS["HungerGames"]

            embed.add_field(name="Coins", value=hunger.get("coins"), inline=True)
            embed.add_field(name="\uFEFF", value=f"\uFEFF")
            embed.add_field(name="Wins", value=hunger.get("wins"), inline=True)

            kills = hunger.get("kills")
            deaths = hunger.get("deaths")
            embed.add_field(name="Kills", value=kills if kills is not None else 0, inline=True)
            embed.add_field(name="Deaths", value=deaths if deaths is not None else 0, inline=True)
            embed.add_field(name="KDR", value=round(
                (kills if kills is not None else 0 + .00001) / (deaths if deaths is not None else 0 + .00001), 2),
                            inline=True)
            await ctx.send(embed=embed)
        elif stat == "paintball":
            embed.set_author(name=f"{discord.utils.escape_markdown(p.DISPLAY_NAME)}'s Paintball Stats",
                             icon_url=await self.cache.get_player_head(p.UUID))

            paint = p.STATS["Paintball"]

            embed.add_field(name="Coins", value=paint.get("coins"), inline=True)
            embed.add_field(name="\uFEFF", value=f"\uFEFF")
            embed.add_field(name="Wins", value=paint.get("wins"), inline=True)

            kills = paint.get("kills")
            deaths = paint.get("deaths")
            embed.add_field(name="Kills", value=kills if kills is not None else 0, inline=True)
            embed.add_field(name="Deaths", value=deaths if deaths is not None else 0, inline=True)
            embed.add_field(name="KDR", value=round(
                (kills if kills is not None else 0 + .00001) / (deaths if deaths is not None else 0 + .00001), 2),
                            inline=True)

            embed.add_field(name="Shots Fired", value=paint.get("shots_fired"), inline=False)
            await ctx.send(embed=embed)
        elif stat == "quake":
            embed.set_author(name=f"{discord.utils.escape_markdown(p.DISPLAY_NAME)}'s Quake Stats",
                             icon_url=await self.cache.get_player_head(p.UUID))

            quake = p.STATS["Quake"]

            embed.add_field(name="Coins", value=quake.get("coins"), inline=True)
            embed.add_field(name="\uFEFF", value=f"\uFEFF")
            embed.add_field(name="Wins", value=quake.get("wins"), inline=True)

            kills = quake.get("kills")
            deaths = quake.get("deaths")
            embed.add_field(name="Kills", value=kills if kills is not None else 0, inline=True)
            embed.add_field(name="Deaths", value=deaths if deaths is not None else 0, inline=True)
            embed.add_field(name="KDR", value=round(
                (kills if kills is not None else 0 + .00001) / (deaths if deaths is not None else 0 + .00001), 2),
                            inline=True)

            embed.add_field(name="Shots Fired", value=quake.get("shots_fired"), inline=False)
            embed.add_field(name="Headshots", value=quake.get("headshots"), inline=False)
            embed.add_field(name="Highest Killstreak", value=quake.get("highest_killstreak"), inline=False)
            await ctx.send(embed=embed)
        elif stat == "uhc":
            embed.set_author(name=f"{discord.utils.escape_markdown(p.DISPLAY_NAME)}'s UHC Stats",
                             icon_url=await self.cache.get_player_head(p.UUID))
        elif stat == "bedwars":
            embed.set_author(name=f"{discord.utils.escape_markdown(p.DISPLAY_NAME)}'s Bedwars Stats",
                             icon_url=await self.cache.get_player_head(p.UUID))

            bedwars = p.STATS["Bedwars"]

            embed.add_field(name="XP", value=bedwars.get("Experience"))
            embed.add_field(name="Coins", value=bedwars.get("coins"))
            embed.add_field(name="Total Games",
                            value=sum({k: v for k, v in bedwars.items() if "games_played" in k}.values()))

            embed.add_field(name="Losses", value=bedwars.get("beds_lost_bedwars"))
            embed.add_field(name="Wins", value=bedwars.get("wins_bedwars"))
            embed.add_field(name="Winstreak", value=bedwars.get("winstreak"))

            kills = bedwars.get("kills_bedwars")
            deaths = bedwars.get("deaths_bedwars")
            embed.add_field(name="Kills", value=kills if kills is not None else 0)
            embed.add_field(name="Deaths", value=deaths if deaths is not None else 0)
            embed.add_field(name="KDR", value=round(
                (kills if kills is not None else 0 + .00001) / (deaths if deaths is not None else 0 + .00001), 2),
                            inline=True)

            embed.add_field(name="Beds Broken", value=bedwars.get("beds_broken_bedwars"))
            await ctx.send(embed=embed)
        elif stat == "truecombat":
            embed.set_author(name=f"{discord.utils.escape_markdown(p.DISPLAY_NAME)}'s\nTrue Combat Stats",
                             icon_url=await self.cache.get_player_head(p.UUID))

            truecombat = p.STATS["TrueCombat"]

            embed.add_field(name="\uFEFF", value=f"\uFEFF")
            embed.add_field(name="Coins", value=truecombat.get("coins"), inline=True)
            embed.add_field(name="\uFEFF", value=f"\uFEFF")
            await ctx.send(embed=embed)
        elif stat == "tntgames":
            embed.set_author(name=f"{discord.utils.escape_markdown(p.DISPLAY_NAME)}'s TNT Games Stats",
                             icon_url=await self.cache.get_player_head(p.UUID))

            tntgames = p.STATS["TNTGames"]

            embed.add_field(name="Coins", value=tntgames.get("coins"))
            embed.add_field(name="Wins", value=tntgames.get("wins"))
            embed.add_field(name="Winstreak", value=tntgames.get("winstreak"))

            kills = sum({k: v for k, v in tntgames.items() if "kills" in k}.values())
            deaths = sum({k: v for k, v in tntgames.items() if "deaths" in k}.values())
            embed.add_field(name="Kills", value=kills if kills is not None else 0)
            embed.add_field(name="Deaths", value=deaths if deaths is not None else 0)
            embed.add_field(name="KDR", value=round((kills + .00001) / (deaths + .00001), 2))

            embed.add_field(name="TNT Run Record", value=tntgames.get("record_tntrun"), inline=False)
            embed.add_field(name="PvP Run Record", value=tntgames.get("record_pvprun"), inline=False)
            await ctx.send(embed=embed)
        elif stat == "supersmash":
            embed.set_author(name=f"{discord.utils.escape_markdown(p.DISPLAY_NAME)}'s\nSuper Smash Stats",
                             icon_url=await self.cache.get_player_head(p.UUID))

            supersmash = p.STATS["SuperSmash"]

            embed.add_field(name="\uFEFF", value=f"\uFEFF")
            embed.add_field(name="Coins", value=supersmash.get("coins"), inline=True)
            embed.add_field(name="\uFEFF", value=f"\uFEFF")
            await ctx.send(embed=embed)
        elif stat == "murdermystery":
            embed.set_author(name=f"{discord.utils.escape_markdown(p.DISPLAY_NAME)}'s Murder Mystery Stats",
                             icon_url=await self.cache.get_player_head(p.UUID))

            mystery = p.STATS["MurderMystery"]

            embed.add_field(name="Coins", value=mystery.get("coins"), inline=True)
            embed.add_field(name="\uFEFF", value=f"\uFEFF")
            embed.add_field(name="Coins Picked Up", value=mystery.get("coins_pickedup"), inline=True)

            embed.add_field(name="Games", value=mystery.get("games"), inline=True)
            embed.add_field(name="Wins", value=mystery.get("wins"), inline=True)
            embed.add_field(name="Deaths", value=mystery.get("deaths"), inline=True)
            await ctx.send(embed=embed)
        elif stat == "mcgo":
            embed.set_author(name=f"{discord.utils.escape_markdown(p.DISPLAY_NAME)}'s Cops & Crims Stats",
                             icon_url=await self.cache.get_player_head(p.UUID))

            mcgo = p.STATS["MCGO"]

            embed.add_field(name="Coins", value=mcgo.get("coins"), inline=True)
            embed.add_field(name="Wins", value=mcgo.get("game_wins"), inline=True)
            embed.add_field(name="Round Wins", value=mcgo.get("round_wins"), inline=True)

            kills = mcgo.get("kills")
            deaths = mcgo.get("deaths")
            embed.add_field(name="Kills", value=kills if kills is not None else 0, inline=True)
            embed.add_field(name="Deaths", value=deaths if deaths is not None else 0, inline=True)
            embed.add_field(name="KDR", value=round(
                (kills if kills is not None else 0 + .00001) / (deaths if deaths is not None else 0 + .00001), 2),
                            inline=True)

            embed.add_field(name="Shots Fired", value=mcgo.get("shots_fired"), inline=False)
            embed.add_field(name="Cop Kills", value=mcgo.get("cop_kills"), inline=False)
            embed.add_field(name="Criminal Kills", value=mcgo.get("criminal_kills"), inline=False)
            await ctx.send(embed=embed)
        elif stat == "skyclash":
            embed.set_author(name=f"{discord.utils.escape_markdown(p.DISPLAY_NAME)}'s Sky Clash Stats",
                             icon_url=await self.cache.get_player_head(p.UUID))

            clash = p.STATS["SkyClash"]

            embed.add_field(name="Coins", value=clash.get("coins"), inline=True)
            embed.add_field(name="Wins", value=clash.get("wins"), inline=True)
            embed.add_field(name="Losses", value=clash.get("losses"), inline=True)

            kills = clash.get("kills")
            deaths = clash.get("deaths")
            embed.add_field(name="Kills", value=kills if kills is not None else 0, inline=True)
            embed.add_field(name="Deaths", value=deaths if deaths is not None else 0, inline=True)
            embed.add_field(name="KDR", value=round(
                (kills if kills is not None else 0 + .00001) / (deaths if deaths is not None else 0 + .00001), 2),
                            inline=True)

            embed.add_field(name="Kill Streak", value=clash.get("killstreak"), inline=False)
            embed.add_field(name="Win Streak", value=clash.get("win_streak"), inline=False)
            await ctx.send(embed=embed)

    @commands.command(name="friends", aliases=["pf", "pfriends", "playerfriends", "friendsof", "player_friends"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def player_friends(self, ctx, player):
        await ctx.trigger_typing()

        player_friends = await self.cache.get_player_friends(player)
        if not player_friends:
            await ctx.send(embed=discord.Embed(color=self.bot.cc,
                                               description=f"**{discord.utils.escape_markdown(player)}** doesn't have any friends! :cry:"))
            return

        embed = discord.Embed(color=self.bot.cc,
                              title=f"**{discord.utils.escape_markdown(player)}**'s friends ({len(player_friends)} total!)")

        body = ""
        count = 0
        embed_count = 0
        for friend in player_friends:
            try:
                name = await self.cache.get_player_name(friend)
            except aiopypixel.exceptions.exceptions.InvalidPlayerError:
                name = "Unknown User"
            body += f"{discord.utils.escape_markdown(name)}\n\n"
            if count > 20:
                embed.add_field(name="\uFEFF", value=body)
                embed_count += 1
                count = 0
                body = ""
            count += 1
        if count > 0:
            embed.add_field(name="\uFEFF", value=body)
            embed_count += 1

        if len(embed) > 5095 or embed_count > 35:
            await ctx.send(embed=discord.Embed(color=self.bot.cc, description=f"{discord.utils.escape_markdown(player)} has too many friends to show!"))
            return

        await ctx.send(embed=embed)

    @commands.command(name="playerguild", aliases=["pg", "playerg", "pguild", "guildofplayer", "player_guild"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def player_guild(self, ctx, player):
        await ctx.trigger_typing()

        player_guild = await self.cache.get_player_guild(player)

        if player_guild is None:
            await ctx.send(embed=discord.Embed(color=self.bot.cc,
                                               description=f"**{discord.utils.escape_markdown(player)}** isn't in a guild!"))
            return

        g = await self.cache.get_guild(player_guild)

        author = f"{discord.utils.escape_markdown(player)}'s Guild ({discord.utils.escape_markdown(g.NAME)})"

        desc = g.DESCRIPTION
        if desc is None:
            embed = discord.Embed(color=self.bot.cc)
        else:
            length = len(author) + 2
            length = length if length > 30 else 30
            embed = discord.Embed(color=self.bot.cc,
                                  description='\n'.join(
                                      desc[i:i + length] for i in
                                      range(0, len(desc), length)))

        member_count = len(g.MEMBERS)
        coins = g.COINS
        xp = g.EXP
        tag = g.TAG
        created = arrow.Arrow.fromtimestamp(g.CREATED / 1000).humanize()

        embed.set_author(name=author)
        embed.add_field(name="Members", value=member_count, inline=True)
        embed.add_field(name="\uFEFF", value=f"\uFEFF")
        embed.add_field(name="Tag", value=tag, inline=True)
        embed.add_field(name="Coins", value=coins, inline=True)
        embed.add_field(name="\uFEFF", value=f"\uFEFF")
        embed.add_field(name="XP", value=xp, inline=True)
        embed.add_field(name="Created", value=created, inline=False)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Player(bot))
