from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login, logout
from .models import Usuario, Visitante
from .serializers import UsuarioSerializer, LoginSerializer, VisitanteSerializer
# DESHABILITADO - Solo registro físico/manual
# from control_acceso.utils import generar_qr_usuario, generar_qr_visitante
from .permissions import PuedeGestionarUsuarios, EsAdministrativoOInstructor

class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar usuarios
    PERMISOS:
    - Login/Registro: Todos (sin autenticación)
    - Ver perfil propio: Todos autenticados
    - Listar/Modificar usuarios: Solo ADMINISTRATIVO
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def get_permissions(self):
        # Permitir login y registro sin autenticación
        if self.action in ['login', 'create']:
            return [AllowAny()]

        # Ver perfil propio: todos
        if self.action in ['perfil']:
            return [IsAuthenticated()]

        # Gestionar usuarios: solo ADMINISTRATIVO
        if self.action in ['list', 'update', 'partial_update', 'destroy']:
            return [PuedeGestionarUsuarios()]

        return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        """Registro de nuevos usuarios - Simplificado"""
        try:
            # Validar contraseñas coincidan
            password = request.data.get('password')
            password2 = request.data.get('password2')
            
            if not password or not password2:
                return Response(
                    {'error': 'Debes proporcionar ambas contraseñas'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if password != password2:
                return Response(
                    {'error': 'Las contraseñas no coinciden'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(password) < 8:
                return Response(
                    {'error': 'La contraseña debe tener al menos 8 caracteres'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar campos requeridos
            username = request.data.get('username')
            email = request.data.get('email')
            numero_documento = request.data.get('numero_documento')
            tipo_documento = request.data.get('tipo_documento')
            rol = request.data.get('rol')
            
            if not all([username, email, numero_documento, tipo_documento, rol]):
                return Response(
                    {'error': 'Todos los campos son obligatorios'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar que el documento no exista
            if Usuario.objects.filter(numero_documento=numero_documento).exists():
                return Response(
                    {'error': 'Ya existe un usuario con este número de documento'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar que el username no exista
            if Usuario.objects.filter(username=username).exists():
                return Response(
                    {'error': 'Este nombre de usuario ya está en uso'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar que el email no exista
            if Usuario.objects.filter(email=email).exists():
                return Response(
                    {'error': 'Este correo electrónico ya está registrado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear usuario
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                rol=rol,
                tipo_documento=tipo_documento,
                numero_documento=numero_documento,
            )
            
            # Crear token
            token, created = Token.objects.get_or_create(user=usuario)
            
            return Response({
                'id': usuario.id,
                'username': usuario.username,
                'email': usuario.email,
                'rol': usuario.rol,
                'token': token.key,
                'mensaje': 'Usuario registrado exitosamente. Ya puedes iniciar sesión.'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Error al crear el usuario: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        usuario = serializer.validated_data['usuario']
        login(request, usuario)
        token, created = Token.objects.get_or_create(user=usuario)

        return Response({
            'token': token.key,
            'usuario': UsuarioSerializer(usuario).data,
            'mensaje': 'Login exitoso.'
        })
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            request.user.auth_token.delete()
        except:
            pass
        logout(request)
        return Response({'mensaje': 'Logout exitoso.'})
    
    @action(detail=False, methods=['get'])
    def perfil(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def listar_para_acceso(self, request):
        """
        Lista usuarios para control de acceso
        Disponible para: VIGILANCIA, ADMINISTRATIVO, INSTRUCTOR
        """
        # Solo estos roles pueden ver la lista
        if request.user.rol not in ['VIGILANCIA', 'ADMINISTRATIVO', 'INSTRUCTOR']:
            return Response(
                {'error': 'No tienes permisos para ver esta lista'},
                status=status.HTTP_403_FORBIDDEN
            )

        usuarios = Usuario.objects.filter(activo=True).order_by('first_name', 'last_name')
        serializer = self.get_serializer(usuarios, many=True)
        return Response(serializer.data)

    # DESHABILITADO - Solo registro físico/manual
    # @action(detail=True, methods=['get'])
    # def generar_qr(self, request, pk=None):
    #     """
    #     Genera el código QR para un usuario
    #     """
    #     usuario = self.get_object()
    #     qr_base64 = generar_qr_usuario(usuario)
    #
    #     return Response({
    #         'usuario_id': usuario.id,
    #         'nombre': usuario.get_full_name(),
    #         'documento': usuario.numero_documento,
    #         'rol': usuario.get_rol_display(),
    #         'qr_image': qr_base64
    #     })
    #
    # @action(detail=False, methods=['get'])
    # def mi_qr(self, request):
    #     """
    #     Genera el código QR del usuario autenticado
    #     """
    #     qr_base64 = generar_qr_usuario(request.user)
    #
    #     return Response({
    #         'usuario_id': request.user.id,
    #         'nombre': request.user.get_full_name(),
    #         'documento': request.user.numero_documento,
    #         'rol': request.user.get_rol_display(),
    #         'qr_image': qr_base64
    #     })
    
class VisitanteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar visitantes
    PERMISOS: VIGILANCIA, ADMINISTRATIVO e INSTRUCTOR
    """
    queryset = Visitante.objects.all()
    serializer_class = VisitanteSerializer

    def get_permissions(self):
        # Solo VIGILANCIA, ADMINISTRATIVO e INSTRUCTOR pueden gestionar visitantes
        return [EsAdministrativoOInstructor()]

    def perform_create(self, serializer):
        serializer.save(registrado_por=self.request.user)

    # DESHABILITADO - Solo registro físico/manual
    # @action(detail=True, methods=['get'])
    # def generar_qr(self, request, pk=None):
    #     """
    #     Genera el código QR para un visitante
    #     """
    #     visitante = self.get_object()
    #     qr_base64 = generar_qr_visitante(visitante)
    #
    #     return Response({
    #         'visitante_id': visitante.id,
    #         'nombre': visitante.nombre_completo,
    #         'documento': visitante.numero_documento,
    #         'entidad': visitante.entidad,
    #         'qr_image': qr_base64
    #     })