# Vistas SIMPLES para el módulo de incidentes
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Incidente
from .forms import IncidenteForm


# Vista SIMPLE: Listar todos los incidentes
@login_required
def listar_incidentes(request):
    """
    Muestra todos los incidentes
    Los administradores ven todos, los demás solo los suyos
    """
    # Si es admin, ve todos los incidentes
    if request.user.rol == 'ADMINISTRATIVO':
        incidentes = Incidente.objects.all()
    else:
        # Los demás solo ven los que reportaron
        incidentes = Incidente.objects.filter(reportado_por=request.user)

    # Contar por estado
    total = incidentes.count()
    reportados = incidentes.filter(estado='REPORTADO').count()
    en_proceso = incidentes.filter(estado__in=['EN_REVISION', 'EN_PROCESO']).count()
    resueltos = incidentes.filter(estado__in=['RESUELTO', 'CERRADO']).count()

    context = {
        'incidentes': incidentes,
        'total': total,
        'reportados': reportados,
        'en_proceso': en_proceso,
        'resueltos': resueltos,
    }

    return render(request, 'reportes/incidentes_lista.html', context)


# Vista SIMPLE: Crear nuevo incidente
@login_required
def crear_incidente(request):
    """
    Formulario para reportar un nuevo incidente
    Cualquier usuario autenticado puede reportar
    """
    if request.method == 'POST':
        form = IncidenteForm(request.POST, request.FILES)

        if form.is_valid():
            # Guardar pero no commit todavía
            incidente = form.save(commit=False)

            # Asignar el usuario que reporta
            incidente.reportado_por = request.user

            # Si es crítico, asignar automáticamente a admin
            if incidente.gravedad == 'CRITICA':
                from usuarios.models import Usuario
                admin = Usuario.objects.filter(rol='ADMINISTRATIVO').first()
                if admin:
                    incidente.asignado_a = admin

            # Guardar
            incidente.save()

            messages.success(request, f'Incidente "{incidente.titulo}" reportado exitosamente.')
            return redirect('listar_incidentes')
    else:
        form = IncidenteForm()

    context = {
        'form': form
    }

    return render(request, 'reportes/incidente_form.html', context)


# Vista SIMPLE: Ver detalle de un incidente
@login_required
def detalle_incidente(request, pk):
    """
    Muestra los detalles completos de un incidente
    """
    incidente = get_object_or_404(Incidente, pk=pk)

    # Verificar permisos: solo el que reportó o admin pueden ver
    if request.user.rol != 'ADMINISTRATIVO' and incidente.reportado_por != request.user:
        messages.error(request, 'No tienes permiso para ver este incidente.')
        return redirect('listar_incidentes')

    context = {
        'incidente': incidente
    }

    return render(request, 'reportes/incidente_detalle.html', context)


# Vista SIMPLE: Actualizar estado (solo admin)
@login_required
def actualizar_incidente(request, pk):
    """
    Permite al administrador actualizar el estado y acciones
    """
    # Solo admin puede actualizar
    if request.user.rol != 'ADMINISTRATIVO':
        messages.error(request, 'Solo los administradores pueden actualizar incidentes.')
        return redirect('listar_incidentes')

    incidente = get_object_or_404(Incidente, pk=pk)

    if request.method == 'POST':
        # Actualizar estado
        estado = request.POST.get('estado')
        acciones = request.POST.get('acciones_tomadas')
        asignado_a_id = request.POST.get('asignado_a')
        marcar_resuelto = request.POST.get('marcar_resuelto')

        if estado:
            incidente.estado = estado

        if acciones:
            incidente.acciones_tomadas = acciones

        # Asignar a usuario
        if asignado_a_id:
            from usuarios.models import Usuario
            incidente.asignado_a = Usuario.objects.get(id=asignado_a_id)
        elif asignado_a_id == '':
            # Si se deja vacío, quitar asignación
            incidente.asignado_a = None

        # Si se marca como resuelto, guardar fecha
        if marcar_resuelto and not incidente.fecha_resolucion:
            from django.utils import timezone
            incidente.fecha_resolucion = timezone.now()

        incidente.save()
        messages.success(request, 'Incidente actualizado exitosamente.')
        return redirect('detalle_incidente', pk=pk)

    # Obtener usuarios disponibles para asignar
    from usuarios.models import Usuario
    usuarios_disponibles = Usuario.objects.filter(
        activo=True,
        rol__in=['ADMINISTRATIVO', 'INSTRUCTOR', 'BRIGADA']
    )

    context = {
        'incidente': incidente,
        'usuarios_disponibles': usuarios_disponibles
    }

    return render(request, 'reportes/incidente_actualizar.html', context)
