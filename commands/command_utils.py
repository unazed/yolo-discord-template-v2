def arguments(*templ_args, **templ_kwargs):
    def decorator(f):
        async def wrapper(client, message, args):
            if templ_args is None and not templ_kwargs:
                return f(client, message)
            final_args, final_kwargs = [], {}
            if len(args) < len(templ_args):
                return await message.channel.send(f"<@{message.author.id}>, expected more arguments")
            idx = 0
            for idx, _ in enumerate(zip(args, templ_args)):
                pos_arg, templ_arg_ty = _
                try:
                    final_args.append(templ_arg_ty(pos_arg))
                except ValueError:
                    return await message.channel.send(f"<@{message.author.id}>, argument #{idx+1} mismatching type, "
                                                      f"expected type {templ_arg_ty!r}")
            if not templ_kwargs:
                return await f(client, message, *final_args)
            pos_arg_offs = idx
            if len(args[idx:]) > len(templ_kwargs):
                return await message.channel.send(f"<@{message.author.id}>, too many arguments passed")
            for idx, _ in enumerate(zip(args[idx:], templ_kwargs)):
                kwarg, templ_kwarg_key = _
                templ_kwarg_ty = templ_kwargs[templ_kwarg_key]
                try:
                    final_kwargs[templ_kwarg_key] = templ_kwarg_ty(kwarg)
                except ValueError:
                    return await message.channel.send(f"<@{message.author.id}>, kw-argument #{idx+pos_arg_offs+2} "
                                                      f"mismatching type, expected type {templ_kwarg_ty!r}")
            return await f(client, message, *final_args, **final_kwargs)
        return wrapper
    return decorator


def no_arguments(f):
    async def wrapper(client, message, args):
        if args:
            return await message.channel.send(f"<@{message.author.id}>, too many arguments passed")
        return await f(client, message)
    return wrapper


async def send_event(client, ev_name, ev_kwargs, _is_retrying=False):
    full_request = {"event": ev_name, **ev_kwargs}
    client.database_pipe.send(full_request)
    if not client.database_pipe.poll(2):
        raise IOError("failed to send event, database unresponsive")
    resp = client.database_pipe.recv()
    if resp['error'] and resp.get("action", None) == "do-update":
        if _is_retrying:
            raise IOError("Discord seems to be forgetting to send some users")
        await client.insert_database()
        return await send_event(client, ev_name, ev_kwargs, True)
    return resp


def is_whitelisted(client, author, perm):
    for role in author.roles:
        if client.config['specific_role_permissions'].get(str(role.id), None) == perm:
            return True
    return False


def chunk_message(lines):
    result = [""]
    for line in lines:
        if len(result[-1]) + len(line) >= 2000:
            result.append(line)
        else:
            result[-1] += f"{line}\n"
    return result
